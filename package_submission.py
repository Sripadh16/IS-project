"""
package_submission.py - Bundles all required course deliverables, advanced architectural
simulation files, hardware models, and test suites into a single zip archive for submission.
"""

import os
import zipfile

def package_submission():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, "TreasureCache_Final_Submission.zip")
    
    files_to_include = [
        "README.md",
        "TreasureCache_Research_Report.docx",
        "TreasureCache_Research_Report.pdf",
        "TreasureCache_Presentation.pptx",
        "TreasureCache_Presentation.pdf",
        "Video_Explanation_Guide.md",
        "PRESENTATION_SCRIPT.md",
        "build_technical_report.py",
        "build_technical_report_pdf.py",
        "build_presentation.py",
        "export_presentation.ps1"
    ]
    
    sim_dir = os.path.join(base_dir, "simulation")
    sim_files = [
        "cache_model.py",
        "attacks.py",
        "ada_ehb_plus.py",
        "advanced_attacks.py",
        "formal_verification.py",
        "hardware_evaluation.py",
        "run_experiments.py",
        "generate_upgrade_plots.py",
        "test_simulation.py",
        "test_advanced_suite.py",
        "test_formal_verification.py",
        "README.md",
        "simulation_results.json",
        "advanced_attacks_results.json",
        "hardware_metrics.json",
        "analytical_validation.json",
        "fig1_residency.png",
        "fig2_victim_latency.png",
        "fig3_shared_contention.png",
        "fig4_multi_vector_attacks.png",
        "fig5_hardware_breakdown.png",
        os.path.join("rtl", "cam_tag_cell.v"),
        os.path.join("rtl", "retention_alu.v"),
        os.path.join("rtl", "token_bucket_limiter.v")
    ]
    
    print(f"Creating submission archive: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fname in files_to_include:
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath):
                zipf.write(fpath, arcname=fname)
                print(f"  + Added: {fname}")
            else:
                print(f"  ! Warning: {fname} not found")
                
        for sname in sim_files:
            spath = os.path.join(sim_dir, sname)
            if os.path.exists(spath):
                arc = os.path.join("simulation", sname)
                zipf.write(spath, arcname=arc)
                print(f"  + Added: {arc}")
            else:
                print(f"  ! Warning: {sname} not found in simulation/")

    print(f"\n[Success] Archive created: {zip_path} ({os.path.getsize(zip_path) / 1024:.1f} KB)")

if __name__ == '__main__':
    package_submission()
