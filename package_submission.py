"""
package_submission.py - Bundles all required deliverables into a single zip file
for final course submission according to IS_ResearchAnalysis_Instructions.pdf.
"""

import os
import zipfile

def package_submission():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, "TreasureCache_Final_Submission.zip")
    
    files_to_include = [
        "TreasureCache_Research_Report.docx",
        "TreasureCache_Research_Report.pdf",
        "TreasureCache_Presentation.pptx",
        "TreasureCache_Presentation.pdf",
        "Video_Explanation_Guide.md",
        "build_technical_report.py",
        "build_presentation.py"
    ]
    
    sim_dir = os.path.join(base_dir, "simulation")
    sim_files = [
        "cache_model.py",
        "attacks.py",
        "run_experiments.py",
        "README.md",
        "simulation_results.json",
        "fig1_latency_distribution.png",
        "fig2_attack_success_rate.png",
        "fig3_performance_tradeoff.png"
    ]
    
    print(f"Creating submission archive: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add root files
        for fname in files_to_include:
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath):
                zipf.write(fpath, arcname=fname)
                print(f"  + Added: {fname}")
            else:
                print(f"  ! Warning: {fname} not found")
                
        # Add simulation files
        for sname in sim_files:
            spath = os.path.join(sim_dir, sname)
            if os.path.exists(spath):
                arc = os.path.join("simulation", sname)
                zipf.write(spath, arcname=arc)
                print(f"  + Added: {arc}")
            else:
                print(f"  ! Warning: {sname} not found in simulation/")

    print(f"\n[Success] Archive created successfully: {zip_path}")
    print(f"Archive size: {os.path.getsize(zip_path) / 1024:.1f} KB")

if __name__ == '__main__':
    package_submission()

