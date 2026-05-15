from aviation.analytics.safety_dashboard import SafetyDashboard

dashboard = SafetyDashboard()

report = dashboard.generate_report()

print("\n=== SAFETY INTELLIGENCE REPORT ===")
print(report)