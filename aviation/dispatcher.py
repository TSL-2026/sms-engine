# ============================================================
# File: aviation/dispatcher.py
# Version: v2.2.0
# Module: Aviation Decision Dispatcher with Structured Schema
#
# Description:
#   ICAO-inspired aviation safety decision system with:
#   - Structured JSON output format
#   - IMSAFE + PAVE risk signals
#   - ICAO Risk Matrix engine
#   - AI explanation layer
#   - Audit logging with schema validation
# ============================================================

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from aviation.prompts import AVIATION_SYSTEM_PROMPT

logger = logging.getLogger("sms.aviation.dispatcher")
from aviation.client import OpenRouterClient
from aviation.human_factors.imsafe import evaluate_imsafe
from aviation.risk.pave import evaluate_pave
from aviation.risk.risk_matrix import RiskMatrixEngine
from aviation.risk.audit_logger import DecisionAuditLogger
from aviation.risk.risk_calibrator import RiskCalibrator


class AviationDispatcher:
    """
    ICAO-aligned Aviation Decision Support System with Structured Output
    """

    def __init__(self, model: str = "anthropic/claude-3-haiku"):
        self.model = model
        self.client = OpenRouterClient(model=model)
        self.risk_engine = RiskMatrixEngine()
        self.audit_logger = DecisionAuditLogger()
        self.calibrator = RiskCalibrator()

    # ========================================================
    # MAIN ENTRY POINT - STRUCTURED OUTPUT
    # ========================================================
    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Process aviation scenario and return structured safety assessment
        """
        # Input validation
        if not user_input or len(user_input.strip()) < 5:
            return self._error_response("INSUFFICIENT_INPUT", "Provide a valid aviation scenario")

        # Risk analysis
        imsafe_result = evaluate_imsafe(user_input)
        pave_result = evaluate_pave(user_input)
        
        # Risk scoring
        likelihood, severity = self._compute_risk_score(imsafe_result, pave_result)
        risk_result = self.risk_engine.evaluate(likelihood, severity)
        
        # Enforcement
        enforced_state, confidence, mitigations = self._enforce_decision(risk_result)
        
        # Extract structured data
        structured_response = self._build_structured_response(
            user_input=user_input,
            imsafe_result=imsafe_result,
            pave_result=pave_result,
            risk_result=risk_result,
            enforced_state=enforced_state,
            confidence=confidence,
            mitigations=mitigations
        )
        
        # Generate AI explanation (now optional - can be disabled for performance)
        explanation = self._generate_explanation(user_input, structured_response)
        structured_response["ai_explanation"] = explanation
        
        # Audit logging
        self._audit_log(user_input, imsafe_result, pave_result, risk_result, 
                       enforced_state, confidence, explanation, mitigations)
        
        return structured_response

    # ========================================================
    # ENFORCEMENT LOGIC WITH MITIGATIONS
    # ========================================================
    def _enforce_decision(self, risk_result: Dict) -> tuple:
        """
        Determine enforcement state and suggest mitigations
        """
        decision = risk_result["decision"]
        score = risk_result["score"]
        risk_level = risk_result["risk_level"]
        
        # Enforcement state mapping
        if decision == "NO-GO":
            enforced_state = "BLOCKED_BY_SAFETY_ENGINE"
            mitigations = self._get_mitigations_for_risk(risk_level, "no_go")
        elif decision == "MITIGATION REQUIRED":
            enforced_state = "CONDITIONAL_OPERATION"
            mitigations = self._get_mitigations_for_risk(risk_level, "conditional")
        else:
            enforced_state = "CLEARED"
            mitigations = self._get_mitigations_for_risk(risk_level, "cleared")
        
        confidence = max(0, min(100, 100 - (score * 4)))
        
        return enforced_state, confidence, mitigations
    
    def _get_mitigations_for_risk(self, risk_level: str, decision_type: str) -> List[str]:
        """
        Return structured mitigations based on risk level and decision type
        """
        mitigations = []
        
        if risk_level == "EXTREME":
            mitigations = [
                "Cancel or indefinitely postpone operation",
                "Complete crew rest cycle required",
                "Aircraft full maintenance inspection required",
                "Weather hold until conditions improve significantly"
            ]
        elif risk_level == "HIGH":
            mitigations = [
                "Delay operation until conditions improve",
                "Enhanced crew briefing required",
                "Additional fuel reserves mandatory",
                "Consider alternate airport with better conditions"
            ]
        elif risk_level == "MEDIUM":
            mitigations = [
                "Review weather briefings",
                "Confirm crew fitness for duty",
                "Verify aircraft serviceability",
                "Maintain heightened situational awareness"
            ]
        else:  # LOW
            mitigations = [
                "Standard operating procedures apply",
                "Routine crew briefing recommended"
            ]
        
        # Add decision-specific mitigations
        if decision_type == "no_go":
            mitigations.insert(0, "DO NOT PROCEED - Safety overrides operational pressure")
        elif decision_type == "conditional":
            mitigations.insert(0, "Proceed only if ALL mitigations are addressed")
        
        return mitigations

    # ========================================================
    # STRUCTURED RESPONSE BUILDER
    # ========================================================
    def _build_structured_response(
        self,
        user_input: str,
        imsafe_result: Dict,
        pave_result: Dict,
        risk_result: Dict,
        enforced_state: str,
        confidence: int,
        mitigations: List[str]
    ) -> Dict:
        """
        Build structured JSON response with clear schema
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_scenario": user_input,
            "decision": {
                "state": enforced_state,
                "confidence": confidence,
                "risk_level": risk_result["risk_level"],
                "risk_score": risk_result["score"],
                "likelihood": risk_result["likelihood"],
                "severity": risk_result["severity"],
                "icao_decision": risk_result["decision"]
            },
            "risk_factors": {
                "imsafe_flags": imsafe_result.get("risk_flags", []),
                "imsafe_risk_level": imsafe_result.get("risk_level", "UNKNOWN"),
                "pave_flags": {
                    "pilot": pave_result.get("pilot", []),
                    "aircraft": pave_result.get("aircraft", []),
                    "environment": pave_result.get("environment", []),
                    "external": pave_result.get("external", [])
                }
            },
            "mitigations": mitigations,
            "system_version": "v2.2.0",
            "model_used": self.model
        }
    
    # ========================================================
    # AI EXPLANATION GENERATOR
    # ========================================================
    def _generate_explanation(self, user_input: str, structured_data: Dict) -> str:
        """
        Generate human-readable explanation from structured data
        """
        try:
            # Create a prompt from structured data
            explanation_prompt = f"""
Based on this aviation safety assessment, provide a clear operational explanation:

Scenario: {user_input}

Decision: {structured_data['decision']['state']}
Risk Level: {structured_data['decision']['risk_level']} (Score: {structured_data['decision']['risk_score']})
Confidence: {structured_data['decision']['confidence']}%

Risk Factors:
- IMSAFE: {', '.join(structured_data['risk_factors']['imsafe_flags']) or 'None'}
- Environmental: {', '.join(structured_data['risk_factors']['pave_flags']['environment']) or 'None'}
- Aircraft: {', '.join(structured_data['risk_factors']['pave_flags']['aircraft']) or 'None'}

Required Mitigations:
{chr(10).join(f'- {m}' for m in structured_data['mitigations'])}

Provide a concise operational briefing (2-3 sentences) explaining the decision and key concerns.
"""
            messages = [
                {"role": "system", "content": AVIATION_SYSTEM_PROMPT},
                {"role": "user", "content": explanation_prompt}
            ]
            
            result = self.client.chat(messages, model=self.model)
            return self._extract_response(result)
        
        except Exception as e:
            return f"AI explanation temporarily unavailable: {str(e)}"
    
    # ========================================================
    # AUDIT LOGGING
    # ========================================================
    def _audit_log(self, user_input: str, imsafe_result: Dict, pave_result: Dict,
                   risk_result: Dict, enforced_state: str, confidence: int, 
                   explanation: str, mitigations: List[str]):
        """
        Log decision with structured schema for traceability
        """
        audit_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": user_input,
            "assessment": {
                "imsafe": imsafe_result,
                "pave": pave_result,
                "risk_matrix": risk_result
            },
            "decision": {
                "state": enforced_state,
                "confidence": confidence,
                "mitigations": mitigations
            },
            "explanation": explanation,
            "system_version": "v2.2.0",
            "model": self.model
        }
        
        return self.audit_logger.log(audit_record)
    
    # ========================================================
    # RISK SCORING (CALIBRATED ICAO MODEL)
    # ========================================================
    def _compute_risk_score(self, imsafe_result: Dict, pave_result: Dict) -> tuple:
        calibration = self.calibrator.calibration_factors()
        factors = calibration["factors"]
        
        likelihood_multiplier = factors.get("likelihood_multiplier", 1.0)
        severity_multiplier = factors.get("severity_multiplier", 1.0)
        
        # Likelihood from IMSAFE
        risk_flags = len(imsafe_result.get("risk_flags", []))
        if risk_flags == 0:
            likelihood = 1
        elif risk_flags == 1:
            likelihood = 2
        elif risk_flags == 2:
            likelihood = 3
        else:
            likelihood = 5
        likelihood = min(5, int(likelihood * likelihood_multiplier))
        
        # Severity from PAVE
        env = pave_result.get("environment", [])
        aircraft = pave_result.get("aircraft", [])
        severity = 1
        if len(env) > 0:
            severity += 2
        if "High terrain risk environment" in str(env):
            severity += 2
        if len(aircraft) > 0:
            severity += 1
        severity = min(5, int(severity * severity_multiplier))
        
        return likelihood, severity
    
    # ========================================================
    # HELPER METHODS
    # ========================================================
    def _error_response(self, error_code: str, message: str) -> Dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error_code,
            "message": message,
            "decision": {"state": "ERROR", "confidence": 0}
        }
    
    def _extract_response(self, result: dict) -> str:
        try:
            choice = result["choices"][0]
            if choice.get("error"):
                return f"[API ERROR] {choice['error']}"
            return choice["message"]["content"]
        except Exception as e:
            return f"[DISPATCHER ERROR] {str(e)}"