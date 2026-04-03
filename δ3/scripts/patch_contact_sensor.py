"""Patch IsaacLab contact_sensor.py for nested prim hierarchies.

Hylion v6 USD has nested prim hierarchy (Geometry/base/.../ankle_roll)
while BHL biped has flat structure. This patch adds recursive fallback
when standard 1-level search finds no matching prims, and constructs
the correct glob pattern using full prim paths.
"""

import sys

filepath = sys.argv[1]

with open(filepath, "r") as f:
    content = f.read()

# The entire _initialize_impl body search + view creation section
old = """        leaf_pattern = self.cfg.prim_path.rsplit("/", 1)[-1]
        template_prim_path = self._parent_prims[0].GetPath().pathString
        body_names = list()
        for prim in sim_utils.find_matching_prims(template_prim_path + "/" + leaf_pattern):
            # check if prim has contact reporter API
            if "PhysxContactReportAPI" in prim.GetAppliedSchemas():
                prim_path = prim.GetPath().pathString
                body_names.append(prim_path.rsplit("/", 1)[-1])
        # check that there is at least one body with contact reporter API
        if not body_names:
            raise RuntimeError(
                f"Sensor at path '{self.cfg.prim_path}' could not find any bodies with contact reporter API."
                "\\nHINT: Make sure to enable 'activate_contact_sensors' in the corresponding asset spawn configuration."
            )

        # construct regex expression for the body names
        body_names_regex = r"(" + "|".join(body_names) + r")"
        body_names_regex = f"{self.cfg.prim_path.rsplit('/', 1)[0]}/{body_names_regex}"
        # convert regex expressions to glob expressions for PhysX
        body_names_glob = body_names_regex.replace(".*", "*")"""

new = """        leaf_pattern = self.cfg.prim_path.rsplit("/", 1)[-1]
        template_prim_path = self._parent_prims[0].GetPath().pathString
        body_names = list()
        _body_full_paths = []  # store full relative paths for nested hierarchies
        for prim in sim_utils.find_matching_prims(template_prim_path + "/" + leaf_pattern):
            # check if prim has contact reporter API
            if "PhysxContactReportAPI" in prim.GetAppliedSchemas():
                prim_path = prim.GetPath().pathString
                body_names.append(prim_path.rsplit("/", 1)[-1])
        # Fallback: recursive search for nested USD hierarchies (e.g. hylion v6)
        if not body_names:
            import re as _re
            _leaf_re = _re.compile(f"^{leaf_pattern}$")
            _stage = sim_utils.get_current_stage()
            _root = _stage.GetPrimAtPath(template_prim_path)
            if _root.IsValid():
                _frontier = list(_root.GetChildren())
                while _frontier:
                    _child = _frontier.pop(0)
                    if _leaf_re.match(_child.GetName()) and "PhysxContactReportAPI" in _child.GetAppliedSchemas():
                        body_names.append(_child.GetName())
                        # Get path relative to template (e.g. Geometry/base/.../ankle_roll)
                        _rel = _child.GetPath().pathString[len(template_prim_path)+1:]
                        _body_full_paths.append(_rel)
                    _frontier.extend(_child.GetChildren())
        # check that there is at least one body with contact reporter API
        if not body_names:
            raise RuntimeError(
                f"Sensor at path '{self.cfg.prim_path}' could not find any bodies with contact reporter API."
                "\\nHINT: Make sure to enable 'activate_contact_sensors' in the corresponding asset spawn configuration."
            )

        # construct regex/glob expression for the body names
        if _body_full_paths:
            # For nested hierarchies, use full relative paths
            _env_pattern = self.cfg.prim_path.rsplit("/", 1)[0].rsplit("/", 1)[0]  # {ENV_REGEX_NS}
            body_names_regex = r"(" + "|".join(_body_full_paths) + r")"
            body_names_regex = f"{_env_pattern}/{template_prim_path.split('/')[-1]}/{body_names_regex}"
        else:
            body_names_regex = r"(" + "|".join(body_names) + r")"
            body_names_regex = f"{self.cfg.prim_path.rsplit('/', 1)[0]}/{body_names_regex}"
        # convert regex expressions to glob expressions for PhysX
        body_names_glob = body_names_regex.replace(".*", "*")"""

if old in content:
    content = content.replace(old, new)
    with open(filepath, "w") as f:
        f.write(content)
    print("PATCHED OK")
else:
    # Check if already patched
    if "_body_full_paths" in content:
        print("ALREADY PATCHED")
    else:
        print("ERROR: old pattern not found — check file manually")
        # Print first 50 chars around "leaf_pattern" to debug
        idx = content.find("leaf_pattern")
        if idx >= 0:
            print(f"Context at 'leaf_pattern': ...{content[idx:idx+200]}...")
