import os
from rivia.model import Project

def run_automated_ras():
    print("Starting Fully Automated HEC-RAS Execution (using rivia)...")
    
    # ==========================================
    # CONFIGURATION
    # ==========================================
    RAS_PROJECT_PATH = r"C:\HEC RAS\new"
    RAS_PROJECT_FILE = os.path.join(RAS_PROJECT_PATH, "pro1.prj")
    UNSTEADY_FILE_PATH = os.path.join(RAS_PROJECT_PATH, "pro1.u01")
    
    PEAK_FLOW = 2726.5
    # Use the short ID of your plan, e.g., "p01"
    PLAN_SHORT_ID = "Unstadyflowanalysis" 
    
    if not os.path.exists(RAS_PROJECT_FILE):
        print(f"ERROR: Project file not found at {RAS_PROJECT_FILE}")
        return

    # ==========================================
    # 1. Inject Flow into the .u01 File
    # ==========================================
    print("Injecting 100-Year Peak Flow into the unsteady flow file...")
    with open(UNSTEADY_FILE_PATH, 'r') as file:
        lines = file.readlines()

    new_lines = []
    in_hydrograph = False
    
    for line in lines:
        if line.strip().startswith("Flow Hydrograph="):
            in_hydrograph = True
            new_lines.append("Flow Hydrograph= 48 \n") 
            flow_values = [f"{PEAK_FLOW:.2f}"] * 48
            for i in range(0, len(flow_values), 10):
                new_lines.append(" " + " ".join(flow_values[i:i+10]) + " \n")
            in_hydrograph = False
            continue 
        if in_hydrograph and (line.strip()[0].isdigit() or line.strip().startswith('-')):
            continue 
        new_lines.append(line)

    with open(UNSTEADY_FILE_PATH, 'w') as file:
        file.writelines(new_lines)
    print("✅ Unsteady flow file updated.")

    # ==========================================
    # 2. Use rivia to Run the Model
    # ==========================================
    print(f"Opening HEC-RAS project and running plan {PLAN_SHORT_ID}...")
    
    try:
        # Open the project using the correct 'Project' class
        model = Project(RAS_PROJECT_FILE)
        print(f"   Connected to HEC-RAS version: {model.version}")
        
        # Set the active plan by its short ID
        model.set_plan(short_id=PLAN_SHORT_ID)
        
        # Run the simulation. hide_window=False lets you watch it run.
        print("   Computing... (This may take a minute)")
        model.run(hide_window=False)
        
        print("🎉 HEC-RAS Simulation Complete! Open RAS Mapper to see your 100-Year Flood Map.")
        
    except Exception as e:
        print(f"❌ An error occurred while running the model: {e}")

if __name__ == "__main__":
    run_automated_ras()