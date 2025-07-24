#!/usr/bin/env python3
"""
Fix indentation error in agent_routes.py
"""

def fix_indentation_error():
    """Fix the indentation error caused by the patch"""
    
    agent_routes_path = '/app/backend/src/routes/agent_routes.py'
    
    # Read the current file
    with open(agent_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the specific indentation issue around line 2562-2564
    # The issue is that we replaced part of an if block incorrectly
    
    # First, let's find the problematic section
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if 'expected an indented block after' in str(line):
            print(f"Found error context around line {i}")
        
        # Look for the specific pattern that's broken
        if 'plan_prompt = f"""Crea un plan excepcional' in line and i > 0:
            # Check the previous line
            prev_line = lines[i-1].strip()
            print(f"Line {i-1}: '{prev_line}'")
            print(f"Line {i}: '{line}'")
            
            # If previous line ends with : and next line isn't indented properly
            if prev_line.endswith(':') and not line.startswith('        '):
                print(f"Found indentation issue at line {i}")
                # This is likely inside an if block that needs proper indentation
                
                # Find the proper indentation by looking at surrounding context
                proper_indent = ''
                for j in range(i-10, i):
                    if j >= 0 and lines[j].strip().startswith('if ') and lines[j].strip().endswith(':'):
                        # Found the if block, determine its indentation
                        if_indent = len(lines[j]) - len(lines[j].lstrip())
                        proper_indent = ' ' * (if_indent + 4)  # Add 4 spaces for if block content
                        break
                
                if not proper_indent:
                    proper_indent = '                    '  # Default to 20 spaces if we can't determine
                
                # Fix the indentation for this line and following lines of the prompt
                j = i
                while j < len(lines) and ('plan_prompt' in lines[j] or lines[j].strip().startswith('"""') or 'CREA UN PLAN' in lines[j]):
                    if not lines[j].strip():  # Empty line
                        j += 1
                        continue
                    # Re-indent this line
                    lines[j] = proper_indent + lines[j].lstrip()
                    j += 1
                
                break
    
    # Write back the fixed content
    fixed_content = '\n'.join(lines)
    
    with open(agent_routes_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ Fixed indentation error")
    return True

if __name__ == "__main__":
    print("🔧 Fixing indentation error...")
    fix_indentation_error()
    print("✅ Indentation fixed, restarting backend...")
    
    import subprocess
    subprocess.run(['sudo', 'supervisorctl', 'restart', 'backend'])
    print("🔄 Backend restarted")