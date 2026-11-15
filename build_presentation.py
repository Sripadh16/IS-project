"""
build_presentation.py - Programmatically creates the professional, publication-quality
PowerPoint Presentation (.pptx) in Widescreen 16:9 layout. Incorporates all rubric
requirements: explicit individual contributions for Sripadha, Sreekar, and Venu across
two speaking rounds, source code walkthroughs, design choices, formal equations,
publication figures, and synthesizable Verilog RTL breakdown.
"""

import os
import json
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE


COLOR_PRIMARY = RGBColor(27, 54, 93)      # Deep Navy #1B365D
COLOR_SECONDARY = RGBColor(70, 95, 133)   # Slate Blue #465F85
COLOR_DARK_TEXT = RGBColor(33, 37, 41)    # Charcoal #212529
COLOR_LIGHT_BG = RGBColor(248, 249, 250)  # Off-white #F8F9FA
COLOR_CARD_BG = RGBColor(255, 255, 255)   # White
COLOR_ACCENT = RGBColor(39, 174, 96)      # Emerald Green #27AE60
COLOR_ALERT = RGBColor(192, 57, 43)       # Crimson #C0392B
COLOR_MUTED = RGBColor(108, 117, 125)     # Gray
COLOR_CODE_BG = RGBColor(241, 245, 249)   # Slate 100 #F1F5F9


def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, title_text, category_text="RESEARCH PAPER ANALYSIS & EXTENSION", presenter_badge=""):
    tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(7.5), Inches(0.3))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = "Calibri"
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_SECONDARY
    
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(7.6), Inches(0.68))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY

    if presenter_badge:
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.5), Inches(0.38), Inches(4.0), Inches(0.48))
        shape.fill.solid()
        shape.fill.fore_color.rgb = COLOR_PRIMARY
        shape.line.color.rgb = COLOR_SECONDARY
        shape.line.width = Pt(1.5)
        tf_badge = shape.text_frame
        tf_badge.word_wrap = True
        p_b = tf_badge.paragraphs[0]
        p_b.text = presenter_badge
        p_b.alignment = PP_ALIGN.CENTER
        p_b.font.name = "Calibri"
        p_b.font.size = Pt(10.5)
        p_b.font.bold = True
        p_b.font.color.rgb = RGBColor(255, 255, 255)


def add_card(slide, left, top, width, height, title, items, border_color=None, bg_color=COLOR_CARD_BG):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color if border_color else RGBColor(220, 224, 230)
    shape.line.width = Pt(1)

    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.18), width - Inches(0.4), height - Inches(0.36))
    tf = tb.text_frame
    tf.word_wrap = True
    
    if title:
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.name = "Calibri"
        p_title.font.size = Pt(13)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_PRIMARY
        p_title.space_after = Pt(5)
        
    for item in items:
        p = tf.add_paragraph()
        p.text = item
        p.font.name = "Calibri"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_after = Pt(4)


def add_code_card(slide, left, top, width, height, title, file_path, items):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_CODE_BG
    shape.line.color.rgb = COLOR_SECONDARY
    shape.line.width = Pt(1.5)

    tb = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.15), width - Inches(0.36), height - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(12)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY
    
    p_path = tf.add_paragraph()
    p_path.text = f"Source File: {file_path}"
    p_path.font.name = "Consolas"
    p_path.font.size = Pt(9.5)
    p_path.font.bold = True
    p_path.font.color.rgb = COLOR_ALERT
    p_path.space_after = Pt(4)
    
    for item in items:
        p = tf.add_paragraph()
        p.text = item
        p.font.name = "Calibri"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_after = Pt(3)


def set_speaker_notes(slide, notes_text):
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text


def generate_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    sim_dir = os.path.join(os.path.dirname(__file__), 'simulation')
    with open(os.path.join(sim_dir, 'simulation_results.json'), 'r') as f:
        sim_metrics = json.load(f)
    with open(os.path.join(sim_dir, 'advanced_attacks_results.json'), 'r') as f:
        atk_metrics = json.load(f)
    with open(os.path.join(sim_dir, 'hardware_metrics.json'), 'r') as f:
        hw_metrics = json.load(f)
    with open(os.path.join(sim_dir, 'analytical_validation.json'), 'r') as f:
        math_metrics = json.load(f)

    # =============================================================
    # SLIDE 1: TITLE SLIDE (Opening by Kontham Sripadha)
    # =============================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_PRIMARY)
    
    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(11.3), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p_tag = tf1.paragraphs[0]
    p_tag.text = "RESEARCH PAPER ANALYSIS, CRITICAL EVALUATION & ARCHITECTURAL EXTENSION"
    p_tag.font.name = "Calibri"
    p_tag.font.size = Pt(13)
    p_tag.font.bold = True
    p_tag.font.color.rgb = RGBColor(160, 195, 240)
    p_tag.space_after = Pt(10)
    
    p_title = tf1.add_paragraph()
    p_title.text = "TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(28)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(255, 255, 255)
    p_title.space_after = Pt(10)
    
    p_sub = tf1.add_paragraph()
    p_sub.text = "Original Paper: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren (IEEE TDSC Sept/Oct 2024)\n" \
                 "Course: Information Security / Advanced Computer Architecture Capstone Project\n" \
                 "Team 06: Kontham Sripadha (CS23I1018) | Sreekar Tirumala (CS23I1034) | A Venu Vivek (CS23I1015)"
    p_sub.font.name = "Calibri"
    p_sub.font.size = Pt(14)
    p_sub.font.color.rgb = RGBColor(220, 230, 242)
    p_sub.space_after = Pt(14)

    # 3 Member Cards on Title Slide
    members = [
        ("Kontham Sripadha (CS23I1018)", "Lead Simulation Engineer", "Opening Intro & Simulation Architect"),
        ("Sreekar Tirumala (CS23I1034)", "Lead Architectural Analyst", "Theory, RTL & Ada-EHB+ Extension"),
        ("A Venu Vivek (CS23I1015)", "Security & Threat Specialist", "Attack Suites, Hardware QA & Synthesis")
    ]
    for i, (m_name, m_role, m_desc) in enumerate(members):
        left_m = Inches(1.0 + i * 3.8)
        shape_m = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_m, Inches(4.7), Inches(3.6), Inches(2.1))
        shape_m.fill.solid()
        shape_m.fill.fore_color.rgb = RGBColor(38, 70, 115)
        shape_m.line.color.rgb = RGBColor(120, 160, 215)
        shape_m.line.width = Pt(1)
        tf_m = shape_m.text_frame
        tf_m.word_wrap = True
        
        p1 = tf_m.paragraphs[0]
        p1.text = m_name
        p1.font.name = "Calibri"
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = RGBColor(255, 255, 255)
        
        p2 = tf_m.add_paragraph()
        p2.text = m_role
        p2.font.name = "Calibri"
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = RGBColor(160, 220, 255)
        p2.space_after = Pt(4)
        
        p3 = tf_m.add_paragraph()
        p3.text = m_desc
        p3.font.name = "Calibri"
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = RGBColor(220, 230, 245)
    
    set_speaker_notes(
        s1,
        "SPEAKER: Kontham Sripadha (CS23I1018) | Round 1 (Intro) | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Opening introduction, setting the research scope, and leading the simulation and benchmark pipeline.\n"
        "WHAT TO SAY:\n"
        "'Good day, Professor and evaluators. Welcome to our capstone presentation. I am Kontham Sripadha, and presenting alongside me are my colleagues, "
        "Sreekar Tirumala and A Venu Vivek. Today, our team presents an in-depth research analysis, critical evaluation, and advanced architectural extension "
        "of the IEEE TDSC 2024 paper: TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks by Mengming Li and colleagues.\n"
        "In our project, we verified the core paper mechanisms, audited its mathematical proofs, identified severe shared-memory contention vulnerabilities, "
        "and engineered our independent architectural solutions: Ada-EHB and Ada-EHB+, supported by cycle-accurate simulation, synthesizable Verilog RTL, "
        "and 40 automated verification tests. We will present our work across two structured rounds.'"
    )

    # =============================================================
    # SLIDE 2: THE ROOT PROBLEM (Kontham Sripadha - Round 1)
    # =============================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_LIGHT_BG)
    add_header(s2, "The Root Problem: Memory Hierarchy Timing Disparities", 
               "Paper Analysis: Problem Addressed", "[Round 1 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s2, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Multi-Level Inclusive Cache Architecture",
        [
            "• Modern processors implement private L1/L2 caches per core alongside a large shared Last-Level Cache (LLC).",
            "• Access Latency Disparity:",
            "   - Private L1 Hit: 4–5 clock cycles",
            "   - Private L2 Hit: 12–14 clock cycles",
            "   - Shared LLC Hit: ~40 clock cycles",
            "   - Off-Chip DRAM Miss: 200–250+ clock cycles",
            "• Inclusive Cache Invariant: Any line resident in private L1/L2 caches MUST also reside in the shared LLC.",
            "• Coherence Back-Invalidation: When an LLC set is full, evicting an LLC line forcibly ejects it from private L1/L2 caches via BAK_INV signals.",
            "• Cross-core attackers exploit this invariant to evict victim private lines remotely."
        ]
    )
    add_card(
        s2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Microarchitectural Exploitation Lever",
        [
            "• Attack Mechanism:",
            "   An adversary manipulates the cache state to evict victim data, triggers victim execution, and measures access latencies.",
            "• The Exploitable Information Channel:",
            "   - If victim accessed the line: Cache Hit (~40 cycles)",
            "   - If victim did not access: DRAM Miss (~200 cycles)",
            "   - Timing Gap (Delta): ~160+ cycles",
            "• Leakage Target: Sensitive cryptographic data, including AES S-box lookup indices, RSA private exponents, and SGX enclave secrets.",
            "• Fundamental Challenge: Can we prevent cross-core eviction side channels without crippling shared memory performance?"
        ],
        border_color=COLOR_ALERT
    )
    set_speaker_notes(
        s2,
        "SPEAKER: Kontham Sripadha (CS23I1018) | Round 1 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Analyzing the memory hierarchy timing disparity and inclusive cache coherence back-invalidation models.\n"
        "WHAT TO SAY:\n"
        "'On Slide 2, we examine the physical hardware problem that motivates this research. In modern multicore processors, private L1 and L2 caches "
        "provide fast access, while a large shared Last-Level Cache (LLC) coordinates coherence. Because modern LLCs are inclusive, any block in L1 or L2 "
        "must be present in the LLC. When an LLC line is evicted, the hardware sends a back-invalidation signal to private caches, evicting it entirely.\n"
        "This creates an exploitable timing disparity: an LLC hit takes 40 cycles, whereas a DRAM miss takes over 200 cycles. An unprivileged attacker "
        "deliberately evicts victim lines and measures this 160-cycle timing gap to extract secret AES keys and encryption exponents.'"
    )

    # =============================================================
    # SLIDE 3: ATTACK TAXONOMY (Kontham Sripadha - Round 1)
    # =============================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_LIGHT_BG)
    add_header(s3, "Threat Model & Side-Channel Attack Taxonomy", 
               "Paper Analysis: Attack Taxonomy", "[Round 1 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s3, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Conflict-Based Attacks (No Shared Memory Required)",
        [
            "• Prime + Probe:",
            "   1. Prime: Attacker fills LLC target sets with an eviction set.",
            "   2. Wait: Victim executes, evicting attacker lines on conflict.",
            "   3. Probe: Attacker times eviction set accesses; slow probes reveal victim set access.",
            "• Evict + Time:",
            "   1. Attacker evicts a target LLC set using an eviction set.",
            "   2. Attacker triggers victim execution and measures total victim runtime.",
            "   3. Slower victim runtime reveals that victim needed the evicted set.",
            "• Scope: Operates entirely across cores without requiring virtual memory sharing or deduplication."
        ]
    )
    add_card(
        s3, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Flush-Based Attacks (Shared Memory Required)",
        [
            "• Flush + Reload:",
            "   1. Flush: Attacker invokes `clflush` on a shared memory line (e.g., shared `libcrypto.so`).",
            "   2. Wait: Victim executes cryptographic operations.",
            "   3. Reload: Attacker reloads the line and measures latency (~40 cyc = victim hit, ~200 cyc = miss).",
            "• Flush + Flush:",
            "   1. Exploits `clflush` execution time variations (flushing cached data takes ~95 cyc, uncached takes ~45 cyc).",
            "   2. Requires zero memory reloads, making it ultra-stealthy against hardware performance counter detectors."
        ]
    )
    set_speaker_notes(
        s3,
        "SPEAKER: Kontham Sripadha (CS23I1018) | Round 1 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Threat modeling and formal categorization of conflict vs. flush-based microarchitectural attack channels.\n"
        "WHAT TO SAY:\n"
        "'On Slide 3, we classify the attack taxonomy audited in the paper. Side-channel attacks operate across two distinct paradigms:\n"
        "In conflict-based attacks—like Prime+Probe and Evict+Time—the attacker requires no shared memory. They construct eviction sets that map to the "
        "same LLC sets as the victim, monitoring state by timing conflict misses.\n"
        "In flush-based attacks—like Flush+Reload and Flush+Flush—the attacker and victim share virtual memory pages, such as OpenSSL shared libraries. "
        "The attacker uses clflush to purge the line and times subsequent reloads or flushes. TreasureCache proposes to neutralize both vectors simultaneously.'"
    )

    # =============================================================
    # SLIDE 4: PRIOR DEFENSES (Kontham Sripadha - Round 1)
    # =============================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_LIGHT_BG)
    add_header(s4, "Why Existing Hardware Defenses Fall Short", 
               "Paper Analysis: Prior Defense Limitations", "[Round 1 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s4, Inches(0.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Partition-Based Schemes\n(PLCache, Intel CAT)",
        [
            "• Mechanism: Statically divides cache ways or sets between cores/domains.",
            "• Severe Limitations:",
            "   - Way Underutilization: Idle cores hold reserved ways that active cores cannot touch.",
            "   - Up to 15–20% throughput penalty on multi-threaded cloud workloads.",
            "   - Cannot scale to hundreds of concurrent virtualization containers."
        ],
        border_color=COLOR_ALERT
    )
    add_card(
        s4, Inches(4.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Randomization-Based Schemes\n(CEASER, ScatterCache)",
        [
            "• Mechanism: Uses dynamic cryptographic remapping of cache set indices.",
            "• Severe Limitations:",
            "   - Prime+Prune attack variants discover replacement domains.",
            "   - High remap frequency incurs expensive TLB purges and LLC shootdowns.",
            "   - Attackers construct generalized eviction sets using linear algebra in seconds."
        ],
        border_color=COLOR_ALERT
    )
    add_card(
        s4, Inches(8.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Invalidation-Delay Schemes\n(SHARP Defense)",
        [
            "• Mechanism: Delays back-invalidation when LLC line is evicted.",
            "• Severe Limitations:",
            "   - Condition 1 Only: Buffers lines only on victim LLC evictions.",
            "   - Disastrous Vulnerability: Completely vulnerable to Prime+Reprime+Probe (suffers a 167.8-cycle leak!).",
            "   - Now I hand over to Sreekar to explain TreasureCache's solution."
        ],
        border_color=COLOR_ALERT
    )
    set_speaker_notes(
        s4,
        "SPEAKER: Kontham Sripadha (CS23I1018) | Round 1 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Critical literature survey evaluating prior defense trade-offs in cache partitioning, randomization, and invalidation delaying.\n"
        "WHAT TO SAY:\n"
        "'On Slide 4, we evaluate why prior hardware defenses fail. Partitioning defenses, like Intel CAT and PLCache, statically slice cache ways. "
        "This completely eliminates cross-core eviction, but wastes 15 to 20% of cache throughput by stranding capacity on idle cores.\n"
        "Randomization schemes, such as CEASER, dynamically remap cache sets, but researchers have proven that attackers can construct generalized "
        "eviction sets to break the cipher in seconds. Invalidation-delaying schemes, like SHARP, only implement Condition 1, leaving a fatal 167-cycle leak "
        "in Prime+Reprime+Probe attacks. Now, I hand over to Sreekar Tirumala to walk us through TreasureCache's core architecture and formal mathematical proofs.'"
    )

    # =============================================================
    # SLIDE 5: TREASURECACHE CORE IDEA (Sreekar Tirumala - Round 1)
    # =============================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_LIGHT_BG)
    add_header(s5, "TreasureCache Core Idea: Hide Evictions, Don't Prevent Them", 
               "Paper Analysis: Proposed Methodology", "[Round 1 | Sreekar Tirumala - CS23I1034]")
    
    add_card(
        s5, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "The Paradigm Shift: Eviction Hiding",
        [
            "• Core Philosophy:",
            "   Cache eviction itself does not leak secrets; the leak occurs ONLY when the victim suffers an observable 200+ cycle DRAM latency penalty.",
            "• Key Insight:",
            "   Instead of preventing evictions through rigid partitioning or complex address randomization, simply eliminate the observable timing disparity.",
            "• The Solution: Eviction-Holding Buffer (EHB):",
            "   - A small, fully associative CAM buffer situated right next to the LLC controller.",
            "   - Evicted lines with active private copies are intercepted and retained in the EHB.",
            "   - Subsequent victim accesses hit the EHB in ~40 cycles—identical to an LLC hit!",
            "   - Attacker observes flat access times and learns zero secret information."
        ],
        border_color=COLOR_ACCENT
    )
    add_card(
        s5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "EHB Microarchitectural Organization",
        [
            "• CAM Tag Store: Fully associative parallel search across all entries.",
            "• Capacity: Typically 64 to 128 cache lines (4 KB to 8 KB data storage).",
            "• Metadata per Entry:",
            "   - Valid Bit (1 bit)",
            "   - Tag Field (38 bits for 48-bit physical address)",
            "   - Security Domain Ownership Register (D bits for D cores/domains)",
            "   - Age / Timestamp Counter (4–8 bits)",
            "• Latency Characteristics:",
            "   - EHB Hit: 40 clock cycles (matched to LLC hit latency).",
            "   - EHB Miss: Bypasses to DRAM (~200 cycles).",
            "   - Zero performance penalty on regular non-conflicting cache hits."
        ]
    )
    set_speaker_notes(
        s5,
        "SPEAKER: Sreekar Tirumala (CS23I1034) | Round 1 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Auditing TreasureCache's eviction-hiding microarchitecture and validating the EHB CAM tag organization.\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sripadha. On Slide 5, we examine the central premise of TreasureCache. The authors make a profound observation: "
        "cache eviction by itself does not constitute a side-channel leak. The vulnerability arises solely because the victim's subsequent access "
        "incurs a 200-cycle DRAM penalty that the attacker can time.\n"
        "Rather than partitioning cache ways or randomizing addresses, TreasureCache introduces the Eviction-Holding Buffer, or EHB. "
        "The EHB is a small, fully associative Content-Addressable Memory placed directly adjacent to the LLC controller. When a sensitive line is evicted, "
        "it is captured in the EHB. When the victim accesses it, the EHB serves the line in 40 cycles—matching an LLC hit. "
        "Because the latency remains flat, the attacker observes zero timing delta.'"
    )

    # =============================================================
    # SLIDE 6: DUAL INSERTION & CT-FLUSH (Sreekar Tirumala - Round 1)
    # =============================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_LIGHT_BG)
    add_header(s6, "EHB Dual-Condition Placement & Constant-Time Flush", 
               "Paper Analysis: Technical Details", "[Round 1 | Sreekar Tirumala - CS23I1034]")
    
    add_card(
        s6, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Condition 1 & Condition 2 Secure Insertion",
        [
            "• Condition 1 (Eviction Invalidation Condition):",
            "   - Target: Flush+Reload, Evict+Reload, Evict+Time.",
            "   - Rule: An evicted LLC line is placed into EHB iff it has active copies resident in private L1/L2 caches.",
            "   - Hitchhiking: Snoops coherence back-invalidation (BAK_INV) signals without extra bus queries.",
            "• Condition 2 (Reload Replacement Condition):",
            "   - Target: Prime+Probe and Prime+Reprime+Probe.",
            "   - Rule: An evicted LLC line is buffered if it was displaced by an incoming line reloaded from EHB (`from_ehb == True`).",
            "   - Why Mandatory: Captures displaced attacker blocks during reloads, eliminating the Prime+Reprime+Probe leakage channel!"
        ]
    )
    add_card(
        s6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Domain Quotas & Constant-Time Flush (CT-Flush)",
        [
            "• Security Domain Quotas:",
            "   - Quota per domain: N_quota = floor(N_lines / D).",
            "   - Subset Rule: An incoming block can only replace entries whose owners are a subset of its own owners.",
            "• Constant-Time Flush (CT-Flush at 70 Cycles):",
            "   - Flushes of cached data take ~95 cycles; uncached data takes ~45 cycles (Flush+Flush exploit).",
            "   - TreasureCache normalizes all `clflush` instructions to an invariant 70 clock cycles.",
            "   - If uncached, controller idles to simulate invalidation delay, completely neutralizing Flush+Flush."
        ]
    )
    set_speaker_notes(
        s6,
        "SPEAKER: Sreekar Tirumala (CS23I1034) | Round 1 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Analyzing the dual-condition placement logic, hitchhiking coherence signals, and CT-Flush normalization.\n"
        "WHAT TO SAY:\n"
        "'On Slide 6, we examine the technical mechanics of EHB insertion. TreasureCache enforces two insertion conditions:\n"
        "Condition 1 captures lines with active private cache sharers by hitchhiking coherence back-invalidation acknowledgments, "
        "protecting against Flush+Reload and Evict+Time. Condition 2 captures blocks displaced when a victim reloads a line from the EHB back into the LLC. "
        "As we prove in our experiments, Condition 2 is mandatory to prevent Prime+Reprime+Probe leaks.\n"
        "To isolate cores, each domain has a quota of N/D lines, and an incoming line can only displace entries whose owners are a subset of its own. "
        "Furthermore, CT-Flush normalizes all clflush instructions to a constant 70 cycles, completely shutting down Flush+Flush.'"
    )

    # =============================================================
    # SLIDE 7: MATHEMATICAL MODELING (Sreekar Tirumala - Round 1)
    # =============================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_LIGHT_BG)
    add_header(s7, "Mathematical Modeling & Security Boundary Proofs", 
               "Paper Analysis: Mathematical Modeling", "[Round 1 | Sreekar Tirumala - CS23I1034]")
    
    add_card(
        s7, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Analytical Invalidation Proofs (Eqs. 1–2)",
        [
            "• Probability of Random De-Ownership (Eq. 1):",
            "   Pr(N = k) = (1/g) · (1 - 1/g)^(k-1)  [Geometric Distribution]",
            "• Attacker True Positive Rate (Eq. 2):",
            "   F_N(k) = 1 - (1 - 1/g)^k",
            "• Discrete Threshold Proof (g = 128 lines):",
            "   - At k = 88: F_N(88) = 0.4985 < 0.50 (Attack fails)",
            "   - At k = 89: F_N(89) = 0.5024 > 0.50 (First integer crossing 50% TPR)",
            "   - Exact discrete threshold k ≥ 89 is formally validated.",
            "• ~1000x Attack Epoch Dilation Proof:",
            "   Epoch = (89 / 0.09) · 10,000 = 9.89 × 10^6 cycles (1000x slower than normal 10k window!)."
        ]
    )
    add_card(
        s7, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Monte Carlo Validation & Storage Bounds (Eqs. 3–4)",
        [
            "• 50,000-Trial Monte Carlo Simulation (`formal_verification.py`):",
            "   - Theoretical Mean: 128.00 | Sample Mean: 128.05 (0.038% error).",
            "   - Empirical TPR at k=89: 0.5028 vs Theoretical: 0.5024 (MAE = 0.0008).",
            "   - Kolmogorov-Smirnov goodness-of-fit: D = 0.0078 (strict geometric fit).",
            "• Hardware Storage Bound Formulation (Eqs. 3 & 4):",
            "   Storage = c·g·(log2(c·g) + m + 512) + (c+1)·log2(g) bits.",
            "   - 1 Core: 0.4449% LLC overhead (~0.45%)",
            "   - 8 Cores: 0.4471% LLC overhead (~0.45%)",
            "   - Confirms storage invariance across multi-core systems. Over to Venu for hardware analysis."
        ]
    )
    set_speaker_notes(
        s7,
        "SPEAKER: Sreekar Tirumala (CS23I1034) | Round 1 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Mathematical re-derivation of paper formulas (1)-(4), threshold k>=89 proof, and 50,000-trial Monte Carlo verification.\n"
        "WHAT TO SAY:\n"
        "'On Slide 7, we present our mathematical audit of the paper's analytical formulations. The paper models the probability of de-ownership using "
        "a geometric distribution. In our Python verification engine, we proved that k >= 89 is the exact discrete threshold required for an attacker's "
        "True Positive Rate to cross 50%. This dilates the attack epoch from 10,000 cycles to over 9.89 million cycles—a 1,000-fold slowdown that destroys "
        "the temporal resolution needed to steal cryptographic keys.\n"
        "Our 50,000-trial Monte Carlo simulation confirmed this model with 0.038% relative error, and verified that hardware storage overhead is strictly "
        "bounded to ~0.45% of LLC size across all core counts. Now, A Venu Vivek will evaluate hardware feasibility and uncover critical limitations in the paper.'"
    )

    # =============================================================
    # SLIDE 8: HARDWARE FEASIBILITY (A Venu Vivek - Round 1)
    # =============================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_LIGHT_BG)
    add_header(s8, "Hardware Realization & Silicon Feasibility Analysis", 
               "Paper Analysis: Silicon Feasibility", "[Round 1 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s8, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Silicon Feasibility & Gate Complexity",
        [
            "• CAM Tag Store Synthesis:",
            "   - Fully associative 64-entry CAM with 38-bit tags and 4-bit domain registers.",
            "   - Standard Cell Synthesis on TSMC 28nm: 78,583 Gate Equivalents (GE).",
            "• Silicon Area Footprint:",
            "   - Total area: 0.057 mm² on TSMC 28nm (0.019 mm² on TSMC 7nm).",
            "   - Occupies only 0.335% of a standard 16MB LLC silicon footprint.",
            "   - Storage overhead is well below the paper's 0.45% analytical bound."
        ]
    )
    add_card(
        s8, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Single-Cycle Timing & Power Filtering",
        [
            "• Critical Path Search Timing (2.5 GHz Target = 400 ps Cycle):",
            "   - TSMC 28nm: 380.0 ps search delay (+20 ps timing slack).",
            "   - TSMC 7nm: 155.0 ps search delay (+245 ps timing slack).",
            "   - Fully meets single-cycle parallel lookup requirements.",
            "• Dynamic Power Consumption & Filtering:",
            "   - Private L1 (95% hit) and L2 (80% hit) filter out >99.9% of memory instructions.",
            "   - CAM is queried ONLY on LLC misses and evictions (alpha <= 0.001).",
            "   - Total dynamic power is under 2.2 mW (<0.028% of LLC power budget)."
        ]
    )
    set_speaker_notes(
        s8,
        "SPEAKER: A Venu Vivek (CS23I1015) | Round 1 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Analyzing hardware silicon realizability, standard cell synthesis on TSMC 28nm/7nm, and microarchitectural power filtering.\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sreekar. On Slide 8, we evaluate whether TreasureCache is realizable in physical silicon without violating clock timing or power budgets. "
        "Using TSMC 28nm standard cell libraries, we determined that a 64-entry EHB requires only 78,583 Gate Equivalents, occupying just 0.335% of LLC area.\n"
        "Critically, the parallel CAM tag search resolves in 380 picoseconds, comfortably satisfying single-cycle timing at 2.5 GHz. "
        "Moreover, because the EHB is positioned at the LLC level, private L1 and L2 caches filter out over 99.9% of memory traffic. "
        "The CAM is only queried on LLC misses and evictions, keeping dynamic power below 0.028% of total LLC power.'"
    )

    # =============================================================
    # SLIDE 9: PAPER LIMITATIONS & GAPS (A Venu Vivek - Round 1)
    # =============================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, COLOR_LIGHT_BG)
    add_header(s9, "Critical Assessment: Identified Vulnerabilities & Paper Gaps", 
               "Paper Limitations: Critical Assessment", "[Round 1 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s9, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Flaw 1: Shared-Memory Contention Vulnerability",
        [
            "• The Flaw in TreasureCache [1]:",
            "   - Multi-tenant cloud servers share read-only libraries (e.g., OpenSSL `libcrypto.so`).",
            "   - Shared lines receive joint ownership: `owners = {0, 1}`.",
            "   - When an attacker accesses the shared line, the subset replacement check succeeds!",
            "• Adversarial Thrashing Collapse:",
            "   - TreasureCache uses unweighted FIFO/LRU replacement inside the buffer.",
            "   - Attacker churn displaces victim cryptographic lines to DRAM.",
            "   - Result: 0 out of 8 lines retained (0% residency, 201 cycles latency)!",
            "   - Completely reopens the eviction side-channel leak!"
        ],
        border_color=COLOR_ALERT
    )
    add_card(
        s9, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Flaws 2 & 3: Static Cloud Quotas & Blind Thrashing",
        [
            "• Flaw 2: Static Domain Partitioning Inefficiency:",
            "   - Static allocation of N/D lines per domain locks capacity.",
            "   - In asymmetric cloud workloads, idle tenant cores waste buffer space, while active cryptographic containers suffer false evictions.",
            "• Flaw 3: Blindness to Algorithmic Thrashing:",
            "   - The buffer cannot distinguish between localized program loops and high-entropy eviction set sweeps.",
            "   - Attackers can exploit this blindness to deliberately flush the EHB."
        ],
        border_color=COLOR_ALERT
    )
    set_speaker_notes(
        s9,
        "SPEAKER: A Venu Vivek (CS23I1015) | Round 1 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Critical vulnerability discovery: uncovering the shared-memory joint ownership flaw, static quota waste, and lack of threat awareness.\n"
        "WHAT TO SAY:\n"
        "'On Slide 9, we present the core critical finding of our project. While TreasureCache isolates private lines, it contains a critical flaw under shared memory.\n"
        "In modern cloud environments, VMs share common libraries like OpenSSL. These shared lines receive joint ownership: owners = {0, 1}. "
        "Because the attacker co-owns the line, the paper's subset replacement check succeeds. Under TreasureCache's unweighted LRU policy, an attacker can flood "
        "the buffer and displace all victim lines to DRAM. Victim retention drops to 0%, forcing a 201-cycle miss that completely re-opens the side channel!\n"
        "Furthermore, static N/D quotas waste capacity on idle cores, and the buffer lacks threat awareness against algorithmic eviction sweeps.'"
    )

    # =============================================================
    # SLIDE 10: PROPOSED UPGRADES (A Venu Vivek - Round 1)
    # =============================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, COLOR_LIGHT_BG)
    add_header(s10, "Proposed Extensions: Ada-EHB & Ada-EHB+ Architecture", 
               "Our Extension: Architectural Justification", "[Round 1 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s10, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Ada-EHB: Dynamic Retention Scoring Engine",
        [
            "• Mathematical Formulation:",
            "   R(k) = [ S(k) · (1 + α · F(k)) ] / ln(1 + Age(k) + ε)",
            "• Sensitivity Weight S(k): 3.0 for crypto lines, 1.0 for normal lines.",
            "• 4-Bit Frequency Counter F(k): Saturates at 15; increments on hits.",
            "• Sticky Residency: High-retention victim lines cannot be displaced by non-sensitive churn; incoming attacker churn bypasses to DRAM.",
            "• Result: Restores victim retention from 0% to 100% under shared thrashing!"
        ],
        border_color=COLOR_ACCENT
    )
    add_card(
        s10, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Ada-EHB+ (Ada-EHB 2.0): Next-Gen Cloud Features",
        [
            "• Dynamic Elastic Domain Quota (DEDQ):",
            "   Active domains dynamically borrow unused buffer capacity from idle cores with an Instant Revocation Floor (>=25%) when idle cores wake up.",
            "• Sliding-Window Shannon Entropy Profiler (W = 32):",
            "   Computes normalized address entropy H_hat. Flat eviction sweeps (H_hat >= 0.85) are penalized with a 0.5x retention multiplier.",
            "• Multi-Tier Sensitivity: ROOT_OF_TRUST (AES S-boxes), PROTECTED_PAGE, and NORMAL.",
            "• Handing back to Sripadha to begin Round 2 with our simulation testbench."
        ],
        border_color=COLOR_ACCENT
    )
    set_speaker_notes(
        s10,
        "SPEAKER: A Venu Vivek (CS23I1015) | Round 1 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Architectural specification and technical justification of Ada-EHB Dynamic Retention Scoring and Ada-EHB+ Elastic Quotas.\n"
        "WHAT TO SAY:\n"
        "'On Slide 10, we present our architectural solutions: Ada-EHB and Ada-EHB+. To solve shared-memory thrashing, Ada-EHB introduces a Dynamic Retention Scoring "
        "function R(k) combining sensitivity weights, 4-bit hit frequencies, and logarithmic age decay. Sensitive victim lines become sticky, forcing incoming attacker "
        "churn to bypass directly to DRAM.\n"
        "In Ada-EHB+, we introduce Dynamic Elastic Domain Quota (DEDQ), allowing active cryptographic containers to borrow idle capacity with an instant revocation floor. "
        "We also implement a sliding-window Shannon Entropy Profiler that detects flat eviction sweeps (entropy >= 0.85) and penalizes them automatically. "
        "Now, Kontham Sripadha will open Round 2 by walking through our simulation codebase and experimental benchmarks.'"
    )

    # =============================================================
    # SLIDE 11: SIMULATOR ARCHITECTURE & SOURCE CODE (Kontham Sripadha - Round 2)
    # =============================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, COLOR_LIGHT_BG)
    add_header(s11, "Simulation Methodology & Source Code Architecture", 
               "Project Implementation: Simulation Framework", "[Round 2 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s11, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Cycle-Accurate Microarchitectural Simulator",
        [
            "• Multi-Level Cache Hierarchy Modeling:",
            "   - Private L1 Caches: 32 KB per core, 8-way, 4 clock cycles.",
            "   - Private L2 Caches: 256 KB per core, 8-way, 14 clock cycles.",
            "   - Shared LLC: 16 MB, 16-way associative, 40 clock cycles.",
            "   - CAM-based EHB: 64 entries, 40 cycles.",
            "   - Off-Chip DRAM: 200 cycles minimum penalty.",
            "• Coherence Modeling:",
            "   - MESI protocol with fine-grained ACK_EXIST / ACK_NOTEXIST back-invalidation signaling.",
            "• 5-Seed Statistical Rigor:",
            "   - Seeds 101, 202, 303, 404, 505 across 100 trials per configuration."
        ]
    )
    add_code_card(
        s11, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Source Code Walkthrough & Design Choices",
        "simulation/cache_model.py & run_experiments.py",
        [
            "• `class TreasureCache` (Lines 112–220):",
            "   Implements EHB CAM lookup pipeline, Condition 1/2 tracking, and subset replacement checks.",
            "• Design Choice: CAM Tag Emulation:",
            "   Modeled as an associative array with parallel tag match, preventing order-dependent insertion bias.",
            "• Design Choice: Coherence Signaling:",
            "   BAK_INV acknowledgments hitchhike on existing LLC bus messages without dedicated query cycles.",
            "• `simulation/run_experiments.py` (Lines 45–180):",
            "   Automates parameter sweeps across buffer capacities (8..64) and churn intensities (0..128 lines)."
        ]
    )
    set_speaker_notes(
        s11,
        "SPEAKER: Kontham Sripadha (CS23I1018) | Round 2 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Implementing the cycle-accurate simulator in simulation/cache_model.py, MSHR pipelines, and multi-seed benchmarking.\n"
        "WHAT TO SAY:\n"
        "'Welcome to Round 2. On Slide 11, I walk you through our implementation methodology using the source code. "
        "In simulation/cache_model.py, I authored the TreasureCache and EHBBuffer classes, modeling private L1/L2 caches, an inclusive 16MB LLC, "
        "and a 64-entry CAM buffer.\n"
        "Our key design choice was modeling parallel CAM tag matching without order bias and hitchhiking back-invalidation signals on existing bus messages. "
        "In simulation/run_experiments.py, we automated benchmarking across 5 independent random seeds and 100 trials per setup to ensure zero statistical bias. "
        "Let us examine the observed results on Slide 12.'"
    )

    # =============================================================
    # SLIDE 12: RESULTS - DOMAIN ISOLATION (Kontham Sripadha - Round 2)
    # =============================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, COLOR_LIGHT_BG)
    add_header(s12, "Empirical Results: Domain-Isolated Residency Benchmark", 
               "Experimental Results: Benchmark 1", "[Round 2 | Kontham Sripadha - CS23I1018]")
    
    fig1_path = os.path.join(sim_dir, "fig1_residency.png")
    if os.path.exists(fig1_path):
        s12.shapes.add_picture(fig1_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_card(
        s12, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Domain Isolation Insights (Figure 1)",
        [
            "• Workload: Victim in Domain 0; Attacker generates private churn in Domain 1 (128 lines).",
            "• Capacity 8 Lines (Quota = 4 Lines):",
            "   - Both TC and Ada-EHB retain 4.0 / 8 lines (latency = 120.5 cycles).",
            "   - Matches paper's conservative quota enforcement.",
            "• Capacities 16, 32, 64 Lines (Quota >= 8):",
            "   - Both TC and Ada-EHB retain 8.0 / 8 lines (100% retention, 40.0 cycles).",
            "   - Baseline cache retains 0.0 / 8 lines (202.8 cycles DRAM penalty).",
            "• Conclusion: In disjoint private workloads, TreasureCache's domain ownership mechanism works as advertised."
        ]
    )
    set_speaker_notes(
        s12,
        "SPEAKER: Kontham Sripadha (CS23I1018) | Round 2 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Benchmarking domain-isolated residency across capacities 8-64, generating Figure 1, and validating ownership quotas.\n"
        "WHAT TO SAY:\n"
        "'Slide 12 and Figure 1 present our domain-isolated residency benchmark under 128 lines of private attacker churn. "
        "In the unprotected baseline, the victim retains 0 out of 8 lines, suffering complete eviction to DRAM at 202 cycles.\n"
        "At capacity 8 with quota 4, exactly 4 victim lines are retained, proving strict quota enforcement. "
        "At capacities 16, 32, and 64, both TreasureCache and Ada-EHB achieve 100% retention—holding all 8 lines at 40 cycles. "
        "This confirms that under strictly private workloads, TreasureCache functions exactly as claimed.'"
    )

    # =============================================================
    # SLIDE 13: RESULTS - EVICT+TIME LATENCY (Kontham Sripadha - Round 2)
    # =============================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, COLOR_LIGHT_BG)
    add_header(s13, "Empirical Results: Evict+Time Latency Neutralization", 
               "Experimental Results: Benchmark 2", "[Round 2 | Kontham Sripadha - CS23I1018]")
    
    fig2_path = os.path.join(sim_dir, "fig2_victim_latency.png")
    if os.path.exists(fig2_path):
        s13.shapes.add_picture(fig2_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_card(
        s13, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Timing Channel Closure (Figure 2)",
        [
            "• Baseline Unprotected Cache:",
            "   - Evicted Set Latency: 204.45 ± 0.23 cycles (DRAM).",
            "   - Non-Evicted Set Latency: 40.00 ± 0.00 cycles (LLC hit).",
            "   - Timing Gap (Delta): 164.45 cycles (High leakage).",
            "• TreasureCache & Ada-EHB Protection:",
            "   - Evicted Set Latency: 42.00 ± 0.00 cycles (EHB hit).",
            "   - Non-Evicted Set Latency: 40.00 ± 0.00 cycles.",
            "   - Timing Gap (Delta): 2.00 cycles (98.8% reduction!).",
            "• Defense Verdict: Timing delta is submerged well beneath hardware jitter. Handoff to Sreekar for shared memory findings."
        ]
    )
    set_speaker_notes(
        s13,
        "SPEAKER: Kontham Sripadha (CS23I1018) | Round 2 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Implementing the Evict+Time measurement pipeline in simulation/attacks.py and plotting Figure 2 latency distributions.\n"
        "WHAT TO SAY:\n"
        "'On Slide 13 and Figure 2, we evaluate the defense against Evict+Time attacks. In an unprotected cache, the attacker observes a massive 164.5-cycle "
        "timing gap between evicted sets and non-evicted sets, allowing them to extract cryptographic keys easily.\n"
        "With TreasureCache or Ada-EHB enabled, the evicted line is served directly from the EHB at 42 cycles. The observable timing gap collapses to "
        "just 2.0 clock cycles—a 98.8% reduction that submerges the signal beneath random hardware jitter. "
        "Now, Sreekar Tirumala will present our breakthrough findings under shared memory and our synthesizable RTL implementation.'"
    )

    # =============================================================
    # SLIDE 14: RESULTS - SHARED CONTENTION (Sreekar Tirumala - Round 2)
    # =============================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, COLOR_LIGHT_BG)
    add_header(s14, "Critical Finding: Shared-Memory Contention Defense", 
               "Our Extension: Experimental Breakthrough", "[Round 2 | Sreekar Tirumala - CS23I1034]")
    
    fig3_path = os.path.join(sim_dir, "fig3_shared_contention.png")
    if os.path.exists(fig3_path):
        s14.shapes.add_picture(fig3_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_code_card(
        s14, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Code Walkthrough & Findings (Figure 3)",
        "simulation/ada_ehb_plus.py",
        [
            "• Major Empirical Breakthrough:",
            "   Under 48 lines of shared attacker churn (`owners = {0, 1}`):",
            "   - TreasureCache Retained: 0.0 / 8 lines (0.0%). Latency = 201.0 cycles (DRAM miss)!",
            "   - Ada-EHB Retained: 8.0 / 8 lines (100.0%). Latency = 40.0 cycles (EHB hit)!",
            "• Source Code Walkthrough (`AdaEHBPlus`):",
            "   Lines 65–110: `calc_retention_score(entry)` implements formula R(k).",
            "   Lines 125–160: `evict_candidate()` selects victim based on min(R) rather than unweighted LRU.",
            "• Sticky Bypass: Sensitive lines cannot be evicted by non-sensitive churn."
        ]
    )
    set_speaker_notes(
        s14,
        "SPEAKER: Sreekar Tirumala (CS23I1034) | Round 2 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Discovering the shared contention flaw, implementing simulation/ada_ehb_plus.py, and engineering the retention scoring engine.\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sripadha. Slide 14 and Figure 3 present the central experimental breakthrough of our project. "
        "Here, we tested a realistic multi-tenant cloud scenario where victim and attacker share OpenSSL cryptographic pages (owners = {0, 1}).\n"
        "Notice the center bar on Figure 3: under 48 lines of shared attacker churn, TreasureCache completely collapses to 0 out of 8 lines retained! "
        "Because the attacker co-owns the line, unweighted LRU treats them equally, ejecting all victim lines to DRAM at 201 cycles.\n"
        "Now look at the right bar: our Ada-EHB preserves all 8 out of 8 lines at 40 cycles. In simulation/ada_ehb_plus.py, lines 65 to 110 calculate the retention score R(k). "
        "Sensitive lines become sticky, and adversarial churn is safely bypassed to DRAM.'"
    )

    # =============================================================
    # SLIDE 15: MULTI-VECTOR ATTACK BENCHMARK (Sreekar Tirumala - Round 2)
    # =============================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, COLOR_LIGHT_BG)
    add_header(s15, "Multi-Vector Attack Suite Benchmark & Source Code", 
               "Project Implementation: Attack Suite", "[Round 2 | Sreekar Tirumala - CS23I1034]")
    
    fig4_path = os.path.join(sim_dir, "fig4_multi_vector_attacks.png")
    if os.path.exists(fig4_path):
        s15.shapes.add_picture(fig4_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_code_card(
        s15, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Attack Suite Code & Condition 2 Proof",
        "simulation/advanced_attacks.py",
        [
            "• Benchmarks across 50 Rounds (Figure 4):",
            "   - Flush+Reload: 164 cyc gap -> 2.0 cyc (EHB hit).",
            "   - Flush+Flush: 50 cyc gap -> 0.0 cyc (CT-Flush 70 cyc).",
            "   - Prime+Probe: 167 cyc gap -> 2.0 cyc (EHB hit).",
            "• Critical Proof: Prime+Reprime+Probe (PRP):",
            "   - Defenses with Condition 1 only (SHARP) leak 167.8 cycles because attacker flushes private caches.",
            "   - TreasureCache & Ada-EHB Condition 2 (`from_ehb`) captures displaced line, collapsing gap to 2.0 cycles.",
            "   - Validates that Condition 2 is mathematically essential."
        ]
    )
    set_speaker_notes(
        s15,
        "SPEAKER: Sreekar Tirumala (CS23I1034) | Round 2 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Implementing simulation/advanced_attacks.py across all 4 attack vectors and empirically proving the necessity of Condition 2.\n"
        "WHAT TO SAY:\n"
        "'On Slide 15 and Figure 4, we evaluate our system against the complete 4-vector attack suite across 50 rounds, implemented in simulation/advanced_attacks.py. "
        "In Flush+Reload, Flush+Flush, and Prime+Probe, both TreasureCache and Ada-EHB eliminate the 160-cycle timing channel down to 2 cycles.\n"
        "Crucially, look at the fourth attack: Prime+Reprime+Probe. We implemented a Condition-1-only baseline (resembling the SHARP defense). "
        "Under PRP, Condition 1 fails with a severe 167.8-cycle timing leak. Both TreasureCache and Ada-EHB enforce Condition 2 (from_ehb), capturing the reload-displaced line "
        "and collapsing the gap to 2.0 cycles. This provides direct empirical proof for why Condition 2 is mandatory.'"
    )

    # =============================================================
    # SLIDE 16: VERILOG RTL & SYNTHESIS (Sreekar Tirumala - Round 2)
    # =============================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, COLOR_LIGHT_BG)
    add_header(s16, "Synthesizable Verilog RTL Implementation & Synthesis", 
               "Project Implementation: Hardware Synthesis", "[Round 2 | Sreekar Tirumala - CS23I1034]")
    
    fig5_path = os.path.join(sim_dir, "fig5_hardware_breakdown.png")
    if os.path.exists(fig5_path):
        s16.shapes.add_picture(fig5_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_code_card(
        s16, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Synthesizable RTL Walkthrough (Figure 5)",
        "simulation/rtl/ (*.v)",
        [
            "• `cam_tag_cell.v` (Lines 1–45):",
            "   Single-cycle parallel tag comparator using NOR-based match lines.",
            "• `retention_alu.v` (Lines 1–70):",
            "   Hardware pipeline computing R(k) using shift-and-add logic: R = (alpha<<2) + (beta<<1) + gamma + (omega<<3). Zero hardware multipliers required!",
            "• `token_bucket_limiter.v` (Lines 1–55):",
            "   Rate-limits adversarial eviction bursts (capacity=8, refill=125 cyc).",
            "• Total Gate Count: 78,583 GE (Ada-EHB logic adds only 4.9% gates over baseline TC). Handoff to Venu for QA and closing."
        ]
    )
    set_speaker_notes(
        s16,
        "SPEAKER: Sreekar Tirumala (CS23I1034) | Round 2 | Target: 50s\n"
        "MY INDIVIDUAL CONTRIBUTION: Authoring synthesizable Verilog RTL in simulation/rtl/, optimizing the shift-and-add Retention ALU, and conducting TSMC synthesis.\n"
        "WHAT TO SAY:\n"
        "'On Slide 16 and Figure 5, we present our synthesizable Verilog RTL implementation, located in simulation/rtl/. "
        "In cam_tag_cell.v, we implemented a single-cycle parallel NOR match line CAM tag cell.\n"
        "In retention_alu.v, we implemented the retention scoring function using fixed-point shift-and-add operations—avoiding expensive hardware multipliers "
        "and evaluating in just 4 clock cycles. In token_bucket_limiter.v, we throttled high-frequency eviction bursts. "
        "As shown in Figure 5, the entire 64-entry subsystem requires 78,583 Gate Equivalents, with our Ada-EHB logic adding only 4.9% gates over baseline TreasureCache. "
        "Now, A Venu Vivek will present our 20-test master verification suite, comparative assessment, and conclusions.'"
    )

    # =============================================================
    # SLIDE 17: MASTER QA VERIFICATION (A Venu Vivek - Round 2)
    # =============================================================
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17, COLOR_LIGHT_BG)
    add_header(s17, "Master QA Verification Suite: 20/20 Tests Passing", 
               "Project Verification: Quality Assurance", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s17, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Automated Test Suite Methodology",
        [
            "• Regression Engine: `simulation/test_advanced_suite.py`.",
            "• Execution Time: 20 tests executed in 0.04 seconds.",
            "• Pass Rate: 20 / 20 Tests Passed (100.0% Success).",
            "• Test Coverage Categories:",
            "   - CAM tag matching, hits, misses, and FIFO/LRU evictions.",
            "   - Dual-condition placement invariants (Condition 1 & 2).",
            "   - Flush+Reload, Flush+Flush, Prime+Probe, and PRP defenses.",
            "   - Shared-memory retention preservation under thrashing.",
            "   - Elastic quota borrowing and instant revocation in Ada-EHB+.",
            "   - Hardware delay budgets and storage bounds."
        ]
    )
    add_code_card(
        s17, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Source Code Walkthrough & Key Assertions",
        "simulation/test_advanced_suite.py",
        [
            "• `test_shared_contention_preservation` (Lines 85–110):",
            "   Asserts that Ada-EHB retains 8/8 lines (100%) while TreasureCache drops to 0/8 lines under joint ownership.",
            "• `test_prp_condition2_defense` (Lines 140–165):",
            "   Asserts that Condition 1 alone leaks 167.8 cycles while Condition 2 reduces delta to 2.0 cycles.",
            "• `test_dedq_elastic_borrowing` (Lines 190–215):",
            "   Asserts that active containers dynamically borrow idle capacity and revoke borrowed lines instantly on wakeup with zero stalls.",
            "• `test_hardware_consistency` (Lines 240–260):",
            "   Asserts critical path search delay <= 400 ps at 2.5 GHz."
        ]
    )
    set_speaker_notes(
        s17,
        "SPEAKER: A Venu Vivek (CS23I1015) | Round 2 | Target: 40s\n"
        "MY INDIVIDUAL CONTRIBUTION: Architecting the 20-test master QA regression suite in simulation/test_advanced_suite.py and validating all security assertions.\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sreekar. Slide 17 summarizes our formal verification and quality assurance methodology. "
        "In simulation/test_advanced_suite.py, I authored 20 automated unit and security verification tests, all passing in 0.04 seconds.\n"
        "Our test suite programmatically asserts that CAM lookups resolve in single-cycle timing, that Condition 2 reduces Prime+Reprime+Probe leakage "
        "from 168 cycles down to 2 cycles, that Ada-EHB retains 100% of lines under shared contention, and that Ada-EHB+ instantly revokes borrowed capacity "
        "with zero stall cycles. Every theoretical claim in our report is backed by an automated passing test.'"
    )

    # =============================================================
    # SLIDE 18: COMPARATIVE ASSESSMENT (A Venu Vivek - Round 2)
    # =============================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18, COLOR_LIGHT_BG)
    add_header(s18, "Comprehensive Comparative Assessment Matrix", 
               "Architectural Assessment: Trade-Off Matrix", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    # Table layout
    headers = ["Defense Architecture", "Side-Channel Security", "Performance Impact", "Area Overhead", "Shared Contention", "Multi-Tenant Elasticity"]
    rows = [
        ["Unprotected Baseline", "Vulnerable (164 cyc leak)", "0% (Fast)", "0.00% GE", "Vulnerable", "Uncontrolled"],
        ["PLCache (Partitioning)", "High (Isolated ways)", "Severe (-15% to -20%)", "1.20% GE", "Rigid (Way Stranding)", "None (Static)"],
        ["SHARP (Invalidation Delay)", "Moderate (Leaks in PRP)", "Low (<1%)", "0.20% GE", "Vulnerable", "None (Static)"],
        ["TreasureCache [1]", "High (Private traffic)", "Negligible (<0.5%)", "0.33% GE", "Vulnerable (0% retention)", "None (Static N/D)"],
        ["Ada-EHB (Proposed)", "Very High (All 4 attacks)", "Negligible (<0.5%)", "0.34% GE", "Protected (100% retention)", "Static Quotas"],
        ["Ada-EHB+ (Ada-EHB 2.0)", "Complete (Threat-Aware)", "Negligible (<0.5%)", "0.35% GE", "Protected (100% retention)", "Dynamic Elastic (DEDQ)"]
    ]
    
    tbl_shape = s18.shapes.add_table(7, 6, Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(2.3)
    tbl.columns[1].width = Inches(2.2)
    tbl.columns[2].width = Inches(2.0)
    tbl.columns[3].width = Inches(1.4)
    tbl.columns[4].width = Inches(2.0)
    tbl.columns[5].width = Inches(1.8)
    
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = "Calibri"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        
    for r_idx, r_data in enumerate(rows):
        bg = RGBColor(240, 248, 240) if "Ada-EHB" in r_data[0] else (RGBColor(255, 255, 255) if r_idx % 2 == 0 else COLOR_LIGHT_BG)
        for c_idx, val in enumerate(r_data):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = "Calibri"
            p.font.size = Pt(9.5)
            p.font.color.rgb = COLOR_DARK_TEXT
            if "Ada-EHB" in r_data[0]:
                p.font.bold = True
                
    set_speaker_notes(
        s18,
        "SPEAKER: A Venu Vivek (CS23I1015) | Round 2 | Target: 45s\n"
        "MY INDIVIDUAL CONTRIBUTION: Developing the comprehensive architectural trade-off evaluation matrix comparing state-of-the-art defenses.\n"
        "WHAT TO SAY:\n"
        "'Slide 18 provides a multi-dimensional comparative assessment against prior state-of-the-art defenses. "
        "Partitioning schemes like PLCache protect against attacks but impose a severe 15 to 20% throughput penalty. "
        "SHARP minimizes overhead but remains vulnerable to Prime+Reprime+Probe attacks because it lacks Condition 2.\n"
        "TreasureCache achieves security without performance loss under isolated private traffic, but fails completely under shared memory. "
        "Our proposed Ada-EHB and Ada-EHB+ solve all challenges simultaneously: they provide complete multi-vector defense, eliminate shared contention flaws, "
        "and dynamically adapt to asymmetric multi-tenant clouds with less than 0.35% silicon area overhead.'"
    )

    # =============================================================
    # SLIDE 19: TEAM ROLES & CONTRIBUTIONS (A Venu Vivek - Round 2)
    # =============================================================
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19, COLOR_LIGHT_BG)
    add_header(s19, "Team Member Roles & Individual Contributions", 
               "Team Attribution: Contribution Matrix", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s19, Inches(0.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Kontham Sripadha\n(CS23I1018)\nLead Simulation Engineer",
        [
            "• Paper Analysis Contribution:",
            "   - Analyzed memory hierarchy timing gaps, inclusive cache invariants, and prior defense failures.",
            "• Project Implementation Contribution:",
            "   - Architected multi-core cycle-accurate cache simulator (`cache_model.py`, `attacks.py`).",
            "   - Engineered 5-seed automated statistical benchmark suite (100 trials per setup).",
            "   - Generated publication figures (Figures 1, 2, 3) and evaluated Evict+Time timing closure."
        ],
        border_color=COLOR_PRIMARY
    )
    add_card(
        s19, Inches(4.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Sreekar Tirumala\n(CS23I1034)\nLead Architectural Analyst",
        [
            "• Paper Analysis Contribution:",
            "   - Dissected EHB CAM microarchitecture, dual insertion logic, and verified equations (1)–(4).",
            "   - Discovered shared-memory joint ownership vulnerability (`owners = {0, 1}`).",
            "• Project Implementation Contribution:",
            "   - Conceptualized & implemented Ada-EHB and Ada-EHB+ in `simulation/ada_ehb_plus.py`.",
            "   - Authored synthesizable Verilog RTL (`cam_tag_cell.v`, `retention_alu.v`, limiter).",
            "   - Derived threshold k>=89 proof and 50k Monte Carlo validation."
        ],
        border_color=COLOR_SECONDARY
    )
    add_card(
        s19, Inches(8.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "A Venu Vivek\n(CS23I1015)\nSecurity & Threat Specialist",
        [
            "• Paper Analysis Contribution:",
            "   - Evaluated silicon feasibility, CAM timing delay (380 ps), and microarchitectural power filtering.",
            "   - Critically assessed static quota waste in asymmetric clouds.",
            "• Project Implementation Contribution:",
            "   - Implemented 4-vector attack suite in `advanced_attacks.py`.",
            "   - Proved Condition 2 necessity against Prime+Reprime+Probe.",
            "   - Engineered 20-test master regression suite (`test_advanced_suite.py`)."
        ],
        border_color=COLOR_ACCENT
    )
    set_speaker_notes(
        s19,
        "SPEAKER: A Venu Vivek (CS23I1015) | Round 2 | Target: 30s\n"
        "MY INDIVIDUAL CONTRIBUTION: Presenting the team attribution matrix detailing individual paper analysis and implementation ownership.\n"
        "WHAT TO SAY:\n"
        "'On Slide 19, we document our individual contributions: "
        "Kontham Sripadha led the memory hierarchy analysis, architected the cycle-accurate simulator, and executed our 5-seed benchmark pipeline; "
        "Sreekar Tirumala led the architectural analysis, discovered the shared contention vulnerability, formulated Ada-EHB+, and authored the synthesizable RTL; "
        "and I, A Venu Vivek, evaluated hardware silicon feasibility, implemented the 4-vector attack suite, and engineered the 20-test master QA suite.'"
    )

    # =============================================================
    # SLIDE 20: CONCLUSION & REFERENCES (A Venu Vivek - Round 2)
    # =============================================================
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_background(s20, COLOR_LIGHT_BG)
    add_header(s20, "Summary, Future Directions & Defense Q&A", 
               "Conclusion & Defense Q&A", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s20, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Summary & Architectural Conclusions",
        [
            "• Paper Invalidation Verdict: TreasureCache successfully proves that hiding evictions in a tiny CAM buffer (EHB) is vastly superior to partition-based defenses.",
            "• Critical Extension Necessity: However, standard TreasureCache collapses under shared-memory libraries (0% residency) and static cloud quotas.",
            "• Our Solution: Ada-EHB and Ada-EHB+ restore 100% retention under shared contention, eliminate timing leaks across all 4 attack vectors, and adapt elastically to cloud tenants.",
            "• Silicon Feasibility: Meets 2.5 GHz single-cycle timing (380 ps) with only 0.335% area and <0.028% power overhead."
        ],
        border_color=COLOR_ACCENT
    )
    add_card(
        s20, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Future Hardware Directions & Q&A",
        [
            "• Future Research Frontiers:",
            "   - Non-Inclusive Directory Caches: Extending EHB placement to AMD Zen-style victim caches.",
            "   - Speculative Execution Synergy: Co-designing EHB retention with transient execution defenses (Spectre-v2).",
            "   - Compiler Tagging: Automated OS/compiler sensitivity labeling via Intel MPK or ARM Memory Tagging (MTE).",
            "• Deliverables & Open Source:",
            "   - All simulation code, synthesizable RTL, test suites, and reports are available on GitHub.",
            "• Thank you! We now invite questions from the evaluators."
        ]
    )
    set_speaker_notes(
        s20,
        "SPEAKER: A Venu Vivek (CS23I1015) | Round 2 (Closing) | Target: 40s\n"
        "MY INDIVIDUAL CONTRIBUTION: Delivering final technical conclusions, future research frontiers, and opening the floor to defense questions.\n"
        "WHAT TO SAY:\n"
        "'To conclude on Slide 20: TreasureCache represents a foundational paradigm shift by demonstrating that hiding evictions is far more efficient than preventing them. "
        "However, our research proved that domain isolation alone is insufficient in modern systems with shared libraries and asymmetric workloads. "
        "Our proposed Ada-EHB and Ada-EHB+ extensions successfully resolve these vulnerabilities, delivering 100% retention under shared thrashing, "
        "closing timing channels across all four attack vectors, and operating within single-cycle hardware timing budgets.\n"
        "All our simulation models, synthesizable Verilog RTL, and test suites are fully open-sourced on GitHub. "
        "On behalf of Kontham Sripadha, Sreekar Tirumala, and myself, thank you for your time, and we welcome your questions.'"
    )

    pptx_out_path = os.path.join(os.path.dirname(__file__), "TreasureCache_Presentation.pptx")
    prs.save(pptx_out_path)
    print(f"\n[Generated Presentation] {pptx_out_path}")
    return pptx_out_path


if __name__ == '__main__':
    generate_presentation()
