import os


def generate_nilm_inference_apis_config(config_file):
    print("Configuration for NILM-Inference-APIs")
    print("-------------------------------------")
    nilm_path = input("Absolute path of NILM-Inference-APIs (the parent of its .git directory): ")

    if not os.path.isdir(nilm_path):
        print("Bad path. This will cause troubles in future. Please re-run")
        exit(1)
    else:
        with open(config_file, "w") as f_out:
            f_out.write(nilm_path)
        print(f"Config file was generated successfully at {config_file}")
