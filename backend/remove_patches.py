import glob

files = glob.glob('tests/test_*.py')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    new_lines = []
    skip_indent = False
    
    for line in lines:
        if 'patch("app.security.jwt_validator.get_settings", return_value=test_settings)' in line:
            if line.strip().endswith(':'):
                skip_indent = True
                continue
            else:
                # It is part of a chained patch. Just replace it with a dummy patch.
                line = line.replace('"app.security.jwt_validator.get_settings", return_value=test_settings', '"builtins.sum"')
        
        if skip_indent:
            if line.strip() == '':
                new_lines.append(line)
            elif line.startswith(' ' * 12):
                new_lines.append(line[4:])
            else:
                skip_indent = False
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    with open(f, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)
