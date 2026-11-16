"""
create_final_submission.py - Packages all course deliverables, research reports,
presentation slides, simulation testbenches, synthesizable Verilog RTL, figures,
and the recorded project explanation video (PROJECT_VIDEO.mov) into a single
master archive: Final_Project_Submission.zip
"""

import os
import zipfile
import time

def create_final_submission():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, "Final_Project_Submission.zip")
    
    # Root level deliverable files
    root_files = [
        "README.md",
        "TreasureCache_Research_Report.pdf",
        "TreasureCache_Research_Report.docx",
        "TreasureCache_Presentation.pptx",
        "TreasureCache_Presentation.pdf",
        "PROJECT_VIDEO.mov",
        "Video_Link.txt",
        "PRESENTATION_SCRIPT.md",
        "Video_Explanation_Guide.md",
        "CODE_WALKTHROUGH_GUIDE.md",
        "PROJECT_EXPLANATION.md",
        "simplified.pdf",
        "simplified.docx",
        "build_technical_report.py",
        "build_technical_report_pdf.py",
        "build_presentation.py",
        "build_simplified_doc.py",
        "export_presentation.ps1"
    ]
    
    # Simulation directory files
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
    
    print(f"Creating Master Submission Archive: {zip_path}\n")
    t0 = time.time()
    
    # Use ZIP64 to support files > 2GB
    with zipfile.ZipFile(zip_path, 'w', allowZip64=True) as zipf:
        for fname in root_files:
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath):
                fsize_mb = os.path.getsize(fpath) / (1024 * 1024)
                # Video files are already compressed media; store them to avoid wasting minutes on useless re-compression
                if fname.lower().endswith(('.mov', '.mp4', '.avi', '.mkv')):
                    compress_type = zipfile.ZIP_STORED
                    print(f"  + Bundling Video (Fast Stream): {fname} ({fsize_mb:.1f} MB)...")
                else:
                    compress_type = zipfile.ZIP_DEFLATED
                    print(f"  + Adding Document: {fname} ({fsize_mb:.2f} MB)")
                zipf.write(fpath, arcname=fname, compress_type=compress_type)
            else:
                print(f"  ! Warning: {fname} not found in root")

        for sname in sim_files:
            spath = os.path.join(sim_dir, sname)
            if os.path.exists(spath):
                arc = os.path.join("simulation", sname)
                fsize_kb = os.path.getsize(spath) / 1024
                zipf.write(spath, arcname=arc, compress_type=zipfile.ZIP_DEFLATED)
                print(f"  + Adding Simulation Artifact: {arc} ({fsize_kb:.1f} KB)")
            else:
                print(f"  ! Warning: {sname} not found in simulation/")
                
    elapsed = time.time() - t0
    final_size_gb = os.path.getsize(zip_path) / (1024 ** 3)
    final_size_mb = os.path.getsize(zip_path) / (1024 ** 2)
    
    print(f"\n=======================================================")
    print(f"[SUCCESS] Final Submission Archive Created:")
    print(f"Path: {zip_path}")
    print(f"Total Size: {final_size_mb:.1f} MB ({final_size_gb:.2f} GB)")
    print(f"Packaging Time: {elapsed:.2f} seconds")
    print(f"=======================================================\n")

if __name__ == '__main__':
    create_final_submission()
