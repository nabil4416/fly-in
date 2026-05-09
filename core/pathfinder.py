*** Begin Patch
*** Update File: core/pathfinder.py
@@
-    def __post_init__(self) -> None:
-        """Validate pathfinding result."""
-        if not self.path:
-            raise PathfindingError("Path cannot be empty")
-        if len(self.path) < 2:
-            raise PathfindingError("Path must have at least start and end zone")
-        if self.cost < 1:
-            raise PathfindingError("Cost must be at least 1")
+    def __post_init__(self) -> None:
+        """Validate pathfinding result.
+
+        Validation rules:
+        - A trivial path (start == end) may be represented as a single-element
+          list [start] with cost == 0.
+        - A non-trivial path must have at least two zones and cost >= 1.
+        """
+        if not self.path:
+            raise PathfindingError("Path must have at least one zone")
+        if self.cost < 0:
+            raise PathfindingError("Cost must be at least 0")
@@
-    def is_valid(self) -> bool:
-        """Check if this is a valid path result.
-
-        Returns:
-            True if path has at least 2 zones and cost is positive.
-        """
-        return len(self.path) >= 2 and self.cost >= 1
+    def is_valid(self) -> bool:
+        """Check if this is a valid path result.
+
+        Returns:
+            True if path has at least one zone and cost is non-negative.
+        """
+        return len(self.path) >= 1 and self.cost >= 0
*** End Patch
