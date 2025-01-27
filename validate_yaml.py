import yaml
import sys
import glob
import os


def mandatory(aws_resources, mandatory_list, file_name):
    errors = []
    for aws_resource in aws_resources:
        for mandatory in mandatory_list:
            if mandatory not in aws_resource:
                errors.append(
                    f'In the file {file_name}, the key {mandatory} is not present for the resource {aws_resource["name"]}.')
            elif aws_resource.get(mandatory) is None:
                errors.append(
                    f'In the file {file_name}, the key {mandatory} is present, but its value is missing for the resource {aws_resource["name"]}.')
    return errors


def dependency(aws_resources, dependency_list, file_name):
    errors = []
    for aws_resource in aws_resources:
        for dependency, rules in dependency_list.items():
            if dependency in aws_resource:
                if aws_resource[dependency] == True:  # Condition is True
                    for key in rules.get("mandatory", []):
                        if key not in aws_resource or aws_resource.get(key) is None:
                            errors.append(
                                f'In the file {file_name}, the key {key} is mandatory for the resource {aws_resource["name"]} when {dependency} is true.')
                else:  # Condition is False
                    for key in rules.get("mandatory", []):
                        if key in aws_resource and aws_resource.get(key) is not None:
                            errors.append(
                                f'In the file {file_name}, for the resource {aws_resource["name"]}, {key} is false, but the key {dependency} is incorrectly present..')
    return errors


def type_check(aws_resources, type_list, file_name):
    errors = []
    for aws_resource in aws_resources:
        for key, expected_type in type_list.items():
            if key in aws_resource and aws_resource[key] is not None:
                if type(aws_resource[key]).__name__ != expected_type:
                    errors.append(
                        f'In the file {file_name}, the data type of {key} is incorrect for the resource {aws_resource["name"]}.')
    return errors


def length_check(aws_resources, length_list, file_name):
    errors = []
    for aws_resource in aws_resources:
        for key, length_constraints in length_list.items():
            if key in aws_resource and aws_resource[key] is not None:
                value = aws_resource[key]
                if isinstance(value, (str, int)):
                    value_length = len(str(value))
                    if len(length_constraints) == 1:
                        if value_length != length_constraints[0]:
                            errors.append(
                                f'In the file {file_name}, the length of {key} is incorrect for the resource {aws_resource["name"]}.')
                    elif len(length_constraints) == 2:
                        if not (length_constraints[0] <= value_length <= length_constraints[1]):
                            errors.append(
                                f'In the file {file_name}, the length of {key} is incorrect for the resource {aws_resource["name"]}.')
    return errors


def allowed_values(aws_resources, allowed_list, file_name):
    errors = []
    for aws_resource in aws_resources:
        for key, allowed_value in allowed_list.items():
            if key in aws_resource:
                if aws_resource[key] not in allowed_value:
                    errors.append(f'In the file {file_name}, the value of {key} can be any of {allowed_value} for the resource {aws_resource["name"]}')
    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_yaml.py <conditions_file>")
        sys.exit(1)

    conditions_file = sys.argv[1]

    # List of directories to search for YAML files
    directories_to_check = ["yaml_files", "yaml_files2"]

    # Discover all YAML files in the specified directories and subdirectories
    yaml_files = []
    for directory in directories_to_check:
        yaml_files.extend(list(set(glob.glob(f"{directory}/**/*.yaml", recursive=True))))

    if not yaml_files:
        print("No YAML files found to validate.")
        sys.exit(0)

    with open(conditions_file, 'r') as file:
        conditions = yaml.safe_load(file)

    all_errors = []
    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as file:
            aws_resources = yaml.safe_load(file)

        print(f"Validating {yaml_file}...")
        if "mandatory" in conditions:
            all_errors.extend(mandatory(aws_resources, conditions["mandatory"], yaml_file))
        if "dependency" in conditions:
            all_errors.extend(dependency(aws_resources, conditions["dependency"], yaml_file))
        if "type" in conditions:
            all_errors.extend(type_check(aws_resources, conditions["type"], yaml_file))
        if "length" in conditions:
            all_errors.extend(length_check(aws_resources, conditions["length"], yaml_file))
        if "allowed_values" in conditions:
            all_errors.extend(allowed_values(aws_resources, conditions["allowed_values"], yaml_file))

    if all_errors:
        for error in all_errors:
            print(error)
        sys.exit(1)  # Exit with error status
    else:
        print("Validation successful!")
        sys.exit(0)  # Exit with success status


if __name__ == "__main__":
    main()
