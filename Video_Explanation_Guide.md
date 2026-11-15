# Explanation Video Guide & Rubric Compliance Manual
## TreasureCache & Ada-EHB / Ada-EHB+: Research Analysis, Critical Assessment, and Architectural Extension

> **Course**: Information Security / Hardware Security Capstone  
> **Topic**: Critical Analysis and Extension of *"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"* (Mengming Li et al., IEEE TDSC Sept/Oct 2024)  
> **Extensions**: Ada-EHB (Dynamic Retention Scoring) & Ada-EHB+ (Ada-EHB 2.0 with Elastic Cloud Quotas & Shannon Profiling)  
> **Target Duration**: 10–12 Minutes (20 Slides, Concise & Plain English)  
> **Format**: Slide Presentation + Live Code & Experimental Verification Walkthrough + Webcam Face Overlay  
> **Speaking Format**: **Two Structured Rounds per Presenter**  
> **Speaker Sequence**: **Kontham Sripadha (Intro)** &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek** &rarr; **Kontham Sripadha** &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek**  
> **Full Narration Script**: See [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md) for word-for-word spoken narration for every slide.

---

## 1. Course Rubric Compliance Checklist

This guide strictly implements every requirement specified in **Item 4 (Explanation Video)** of the course project guidelines:

- [x] **Individual Contribution Explained**: Each team member explicitly details their personal contribution to both the research paper analysis and project work during their speaking rounds.
- [x] **Clear Understanding of Paper**: Comprehensively covers the problem addressed (Slide 2), threat model & attack taxonomy (Slide 3), prior defense failures (Slide 4), proposed methodology (Slide 5), important technical details (Slide 6), mathematical modeling & proofs (Slide 7), and silicon feasibility (Slide 8).
- [x] **Critical Limitations Discussed**: Team members critically analyze the shared-memory contention flaw (`owners={0, 1}`), static cloud quota waste, and lack of threat awareness in TreasureCache (Slide 9).
- [x] **Proposed Improvements Justified**: Technical justification for Ada-EHB Dynamic Retention Scoring $R(k)$, Dynamic Elastic Domain Quota (DEDQ), and Shannon Entropy Profiling is detailed with equations and state diagrams (Slide 10).
- [x] **Implementation Methodology & Design Choices Using Source Code**: Dedicated source code walkthroughs and design choices are presented using `simulation/cache_model.py` (Slide 11), `simulation/ada_ehb_plus.py` (Slide 14), `simulation/advanced_attacks.py` (Slide 15), synthesizable Verilog RTL `simulation/rtl/` (Slide 16), and `simulation/test_advanced_suite.py` (Slide 17).
- [x] **Experiments & Observed Results Explained**: Detailed empirical walkthrough of Figure 1 (residency), Figure 2 (latency), Figure 3 (shared contention), Figure 4 (multi-vector attacks), and Figure 5 (hardware synthesis breakdown).
- [x] **PPT + Source Code Supporting Explanation**: Slides feature visual cards, data tables, and embedded source code callout boxes with exact file paths and line ranges.
- [x] **Face & Name Visibility**: Clear protocol for webcam face overlay in Zoom/OBS, student display name banners, and slide presenter badges.

---

## 2. 2-Round Timing Breakdown & Slide Allocation

| Round | Speaker | Roll No. | Primary Role | Presentation Scope | Slides | Target Time |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: |
| **Round 1 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Lead Simulation Engineer | Opening Intro, Problem Addressed, Attack Taxonomy & Prior Defenses | **Slides 1 – 4** | ~3.0 mins |
| **Round 1 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | Lead Architectural Analyst | EHB Proposed Methodology, Dual-Condition Placement & Formal Proofs | **Slides 5 – 7** | ~2.5 mins |
| **Round 1 (Part 3)** | **A Venu Vivek** | `CS23I1015` | Security & Threat Specialist | Silicon Feasibility, Critical Limitations/Gaps & Ada-EHB+ Justification | **Slides 8 – 10** | ~2.5 mins |
| **Round 2 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Lead Simulation Engineer | Implementation Methodology, Code Walkthrough & Benchmarks 1 & 2 | **Slides 11 – 13** | ~2.2 mins |
| **Round 2 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | Lead Architectural Analyst | Shared Contention Finding, Multi-Vector Attacks & Synthesizable RTL | **Slides 14 – 16** | ~2.5 mins |
| **Round 2 (Part 3)** | **A Venu Vivek** | `CS23I1015` | Security & Threat Specialist | 20/20 Test QA Suite, Comparative Matrix, Roles & Defense Q&A | **Slides 17 – 20** | ~2.5 mins |

---

## 3. Zoom / Teams Recording Instructions

1. **Meeting Setup**:
   - Start a Zoom meeting with all 3 members: Kontham Sripadha, Sreekar Tirumala, and A Venu Vivek.
   - Set webcam video to **HD** and ensure all 3 faces are clearly lit.
   - Rename your Zoom participants to: `Full Name (Student ID)` — e.g. `Kontham Sripadha (CS23I1018)`.
2. **Screen Sharing & Recording Options**:
   - In Zoom Settings &rarr; **Recording**:
     - Check **"Record video during screen sharing"**.
     - Check **"Place video next to the shared screen in the recording"**.
   - Share the screen displaying [TreasureCache_Presentation.pptx](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/TreasureCache_Presentation.pptx) in full-screen (16:9).
3. **Screen Switching Protocol during Round 2**:
   - When Sripadha reaches Slide 11, Sreekar reaches Slide 14/16, or Venu reaches Slide 17, you may either reference the **Source Code Reference Box** directly on the slide or use **Alt+Tab** to switch to VS Code for 15–20 seconds to show the live file (`cache_model.py`, `ada_ehb_plus.py`, or `cam_tag_cell.v`).
4. **Live Code Demo Execution (Terminal Commands)**:
   ```powershell
   # Run the 20-test master regression suite
   python simulation/test_advanced_suite.py

   # Run the complete experimental benchmarks
   python simulation/run_experiments.py

   # Run the multi-vector attack suite
   python simulation/advanced_attacks.py
   ```
5. **Saving the Recording**:
   - End the Zoom meeting and let Zoom convert the recording to `.mp4`.
   - Upload the video to Google Drive or YouTube (unlisted) and paste the link into `Video_Link.txt` before final submission.
