# ============================================================
# File: aviation/analytics/safety_dashboard.py
# Version: v1.0.0
# Safety Dashboard for Aviation Analytics
# ============================================================

import json
from datetime import datetime, timezone
from typing import Dict, List, Any

class SafetyDashboard:
    """Safety dashboard for tracking aviation safety metrics"""
    
    def __init__(self):
        self.assessments = []
        self.alerts = []
        self.metrics = {
            "total_assessments": 0,
            "risk_levels": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "EXTREME": 0},
            "go_no_go_decisions": {"GO": 0, "NO-GO": 0, "CONDITIONAL": 0}
        }
    
    def add_assessment(self, assessment_data: Dict[str, Any]):
        """Add a new safety assessment to the dashboard"""
        assessment_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        self.assessments.append(assessment_data)
        
        # Update metrics
        self.metrics["total_assessments"] += 1
        
        # Track risk levels
        risk_level = assessment_data.get('risk', {}).get('risk_level', 'UNKNOWN')
        if risk_level in self.metrics["risk_levels"]:
            self.metrics["risk_levels"][risk_level] += 1
        
        # Track decisions
        decision = assessment_data.get('enforcement', {}).get('state', 'UNKNOWN')
        if decision == "CLEARED":
            self.metrics["go_no_go_decisions"]["GO"] += 1
        elif decision == "BLOCKED_BY_SAFETY_ENGINE":
            self.metrics["go_no_go_decisions"]["NO-GO"] += 1
        elif decision == "CONDITIONAL_OPERATION":
            self.metrics["go_no_go_decisions"]["CONDITIONAL"] += 1
        
        # Check for critical alerts
        if risk_level in ['HIGH', 'EXTREME']:
            self.alerts.append({
                'timestamp': assessment_data['timestamp'],
                'level': risk_level,
                'message': f"Critical risk level detected: {risk_level}",
                'input': assessment_data.get('input', '')
            })
        
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            'metrics': self.metrics,
            'recent_alerts': self.alerts[-5:] if self.alerts else [],
            'last_assessment': self.assessments[-1] if self.assessments else None,
            'total_alerts': len(self.alerts)
        }
    
    def get_alerts(self) -> List[Dict]:
        """Get all active alerts"""
        return self.alerts
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []
    
    def get_trends(self) -> Dict:
        """Get safety trends over time"""
        if not self.assessments:
            return {"message": "No assessments available"}
        
        recent = self.assessments[-10:]  # Last 10 assessments
        trends = {
            "high_risk_count": sum(1 for a in recent if a.get('risk', {}).get('risk_level') in ['HIGH', 'EXTREME']),
            "average_confidence": sum(a.get('enforcement', {}).get('confidence', 0) for a in recent) / len(recent) if recent else 0
        }
        return trends