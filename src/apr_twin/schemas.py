@@
*** Begin Patch
*** Update File: src/apr_twin/schemas.py
@@
     operational_recommendation: str | None = None
+    # Canonical recommendation code to allow stable translation on the frontend.
+    recommendation_code: str | None = None
     turbidity_alert_active: bool = False
     active_alerts: list[str] = Field(default_factory=list)
*** End Patch
