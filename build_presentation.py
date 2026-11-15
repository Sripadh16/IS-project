"""
build_presentation.py - Creates a clean, concise, professional PowerPoint
presentation (16:9 widescreen) using simple, plain English without heavy jargon.
Includes clear presenter badges, simplified slide cards, source code references,
and matched concise speaker notes for each slide across 2 rounds.
"""

import os
import json
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


def add_header(slide, title_text, category_text="COURSE CAPSTONE PROJECT", presenter_badge=""):
    # Category / breadcrumb
    tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(7.5), Inches(0.3))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = "Calibri"
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_SECONDARY
    
    # Title
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(7.6), Inches(0.68))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY

    # Presenter Badge on Top Right
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
        p_title.space_after = Pt(6)
        
    for item in items:
        p = tf.add_paragraph()
        p.text = item
        p.font.name = "Calibri"
        p.font.size = Pt(11)
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
    p_path.text = f"Source Code: {file_path}"
    p_path.font.name = "Consolas"
    p_path.font.size = Pt(9.5)
    p_path.font.bold = True
    p_path.font.color.rgb = COLOR_ALERT
    p_path.space_after = Pt(4)
    
    for item in items:
        p = tf.add_paragraph()
        p.text = item
        p.font.name = "Calibri"
        p.font.size = Pt(10.5)
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

    # =============================================================
    # SLIDE 1: TITLE SLIDE (Opening by Kontham Sripadha)
    # =============================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_PRIMARY)
    
    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.3), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p_tag = tf1.paragraphs[0]
    p_tag.text = "RESEARCH PAPER ANALYSIS, CRITICAL EVALUATION & SYSTEM UPGRADE"
    p_tag.font.name = "Calibri"
    p_tag.font.size = Pt(13)
    p_tag.font.bold = True
    p_tag.font.color.rgb = RGBColor(160, 195, 240)
    p_tag.space_after = Pt(8)
    
    p_title = tf1.add_paragraph()
    p_title.text = "TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(28)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(255, 255, 255)
    p_title.space_after = Pt(8)
    
    p_sub = tf1.add_paragraph()
    p_sub.text = "Assigned Paper: Mengming Li et al. (IEEE TDSC 2024)\n" \
                 "Course: Information Security / Advanced Computer Architecture Capstone\n" \
                 "Team 06: Kontham Sripadha (CS23I1018) | Sreekar Tirumala (CS23I1034) | A Venu Vivek (CS23I1015)"
    p_sub.font.name = "Calibri"
    p_sub.font.size = Pt(13.5)
    p_sub.font.color.rgb = RGBColor(220, 230, 242)
    p_sub.space_after = Pt(14)

    # 3 Member Cards
    members = [
        ("Kontham Sripadha (CS23I1018)", "Lead Simulation Engineer", "Opening Intro, Cache Simulator & Benchmarks"),
        ("Sreekar Tirumala (CS23I1034)", "Lead Architectural Analyst", "Theory, Verilog RTL & Ada-EHB+ Upgrades"),
        ("A Venu Vivek (CS23I1015)", "Security & Threat Specialist", "Attack Suites, Hardware Synthesis & QA Testing")
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
        "SPEAKER: Kontham Sripadha | Round 1 (Intro) | ~35s\n"
        "WHAT TO SAY:\n"
        "'Hello everyone, and welcome to our capstone presentation. I am Kontham Sripadha, presenting alongside Sreekar Tirumala and A Venu Vivek. "
        "Today, we present our research analysis and project implementation of the IEEE 2024 paper: TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks. "
        "In this project, we studied how attackers steal secret keys through CPU cache timing, tested the paper's defense, discovered a critical vulnerability "
        "when memory is shared, and built our own upgraded defense called Ada-EHB to solve it. We will present our work across two quick rounds.'"
    )

    # =============================================================
    # SLIDE 2: THE ROOT PROBLEM (Kontham Sripadha)
    # =============================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_LIGHT_BG)
    add_header(s2, "The Root Problem: Cache Timing Differences", 
               "Paper Analysis: The Vulnerability", "[Round 1 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s2, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Fast Cache vs. Slow Memory",
        [
            "• CPUs have small, fast caches and large, slow main memory (RAM).",
            "• Speed Disparity:",
            "   - Cache Access: ~40 clock cycles (fast).",
            "   - Main Memory Access: ~200+ clock cycles (slow).",
            "• Shared Cache Rule:",
            "   - Data in private CPU cores must also stay in the shared cache.",
            "   - When the shared cache gets full, kicking out data removes it from private caches too.",
            "• The Risk: Attackers can kick victim data out remotely."
        ]
    )
    add_card(
        s2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "How Attackers Steal Secrets",
        [
            "• The Timing Gap: ~160 clock cycles difference.",
            "• Attack Mechanism:",
            "   - Attacker pushes victim data out of the cache.",
            "   - Victim runs and tries to access its data.",
            "   - If data was kicked out, victim runs noticeably slower.",
            "• The Secret Leak:",
            "   - Measuring access time reveals which memory addresses the victim touched.",
            "   - Used to steal AES encryption keys and passwords without special privileges."
        ],
        border_color=COLOR_ALERT
    )
    set_speaker_notes(
        s2,
        "SPEAKER: Kontham Sripadha | Round 1 | ~35s\n"
        "WHAT TO SAY:\n"
        "'On Slide 2, here is the core problem. Modern processors have small, fast on-chip caches and large, slow main memory. "
        "Reading data from the cache takes about 40 clock cycles, but fetching it from main memory takes over 200 cycles. That 160-cycle difference is the security hole. "
        "Because multiple CPU cores share the main cache, an attacker can intentionally kick a victim program's secret data out of the cache. "
        "If the victim later needs that data, it experiences a noticeable delay. By simply timing how long operations take, an attacker can reconstruct secret encryption keys.'"
    )

    # =============================================================
    # SLIDE 3: ATTACK TAXONOMY (Kontham Sripadha)
    # =============================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_LIGHT_BG)
    add_header(s3, "How Cache Attacks Work: Conflict vs. Flush", 
               "Paper Analysis: Attack Taxonomy", "[Round 1 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s3, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Conflict Attacks (No Shared Memory)",
        [
            "• Prime + Probe & Evict + Time:",
            "• Step 1 (Prime): Attacker fills cache sets with dummy data.",
            "• Step 2 (Wait): Victim program executes its encryption task.",
            "• Step 3 (Probe): Attacker accesses its dummy data again.",
            "   - Fast access = Victim did not touch that cache set.",
            "   - Slow access = Victim pushed attacker data out.",
            "• Advantage for Attacker: Works across cores without sharing any files or virtual memory."
        ]
    )
    add_card(
        s3, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Flush Attacks (Shared Memory Required)",
        [
            "• Flush + Reload & Flush + Flush:",
            "• Requirement: Programs share code libraries (e.g., OpenSSL).",
            "• Flush + Reload:",
            "   - Attacker uses `clflush` instruction to remove a shared line.",
            "   - Victim runs cryptographic functions.",
            "   - Attacker reloads: fast means victim used it; slow means it did not.",
            "• Flush + Flush:",
            "   - Times the `clflush` instruction itself without reloading memory."
        ]
    )
    set_speaker_notes(
        s3,
        "SPEAKER: Kontham Sripadha | Round 1 | ~35s\n"
        "WHAT TO SAY:\n"
        "'On Slide 3, cache timing attacks fall into two main groups. First, Conflict attacks, like Prime+Probe. Here, the attacker does not share any memory with the victim. "
        "The attacker simply fills cache lines with dummy data. When the victim runs, it pushes some attacker data out. The attacker times its own data to see which lines became slow, "
        "revealing which cache locations the victim used. Second, Flush attacks, like Flush+Reload. Here, programs share read-only libraries, like OpenSSL. "
        "The attacker removes a shared line using a flush instruction, waits for the victim to run, and reloads it to see if it came back fast.'"
    )

    # =============================================================
    # SLIDE 4: PRIOR DEFENSES (Kontham Sripadha)
    # =============================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_LIGHT_BG)
    add_header(s4, "Why Earlier Hardware Defenses Failed", 
               "Paper Analysis: Prior Defense Limits", "[Round 1 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s4, Inches(0.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Partitioning (PLCache / CAT)",
        [
            "• Idea: Splits cache ways into strict private zones per core.",
            "• Why it Fails:",
            "   - Wastes 15–20% of cache space.",
            "   - Idle cores hold empty space that active programs cannot touch.",
            "   - Cannot scale to dozens of cloud containers."
        ],
        border_color=COLOR_ALERT
    )
    add_card(
        s4, Inches(4.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Randomization (CEASER)",
        [
            "• Idea: Randomly scrambles cache addresses.",
            "• Why it Fails:",
            "   - Attackers quickly learn the scramble pattern using math.",
            "   - Broken within seconds using eviction set algorithms."
        ],
        border_color=COLOR_ALERT
    )
    add_card(
        s4, Inches(8.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Invalidation Delay (SHARP)",
        [
            "• Idea: Delays kicking data out of private caches.",
            "• Why it Fails:",
            "   - Incomplete rules fail in multi-step attacks.",
            "   - Suffers a massive 168-cycle leak in Prime+Reprime+Probe.",
            "   - Sreekar will now explain TreasureCache."
        ],
        border_color=COLOR_ALERT
    )
    set_speaker_notes(
        s4,
        "SPEAKER: Kontham Sripadha | Round 1 | ~35s\n"
        "WHAT TO SAY:\n"
        "'On Slide 4, existing defenses have serious drawbacks: Partitioning schemes split the cache into private slices. While this stops attacks, it wastes 15 to 20% "
        "of cache performance because idle cores hold onto empty space that active programs cannot use. Randomization schemes scramble cache addresses, but attackers quickly "
        "figure out the pattern using mathematical algorithms. Delay schemes, like SHARP, delay kicking out data, but they fail against multi-step attacks. "
        "Now, Sreekar will explain how TreasureCache solves this problem.'"
    )

    # =============================================================
    # SLIDE 5: TREASURECACHE CORE IDEA (Sreekar Tirumala)
    # =============================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_LIGHT_BG)
    add_header(s5, "TreasureCache Core Idea: Hide Evictions, Don't Stop Them", 
               "Paper Methodology: The EHB Concept", "[Round 1 | Sreekar Tirumala - CS23I1034]")
    
    add_card(
        s5, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "A Simpler Approach: Eviction Hiding",
        [
            "• Key Insight:",
            "   Kicking data out of the cache is NOT dangerous by itself.",
            "   The danger happens ONLY when the victim has to wait 200 cycles for slow main memory.",
            "• The TreasureCache Fix:",
            "   - Do not stop evictions.",
            "   - Simply remove the noticeable timing delay.",
            "• The Eviction-Holding Buffer (EHB):",
            "   - A small, fast hardware buffer added next to the cache.",
            "   - When victim data gets kicked out, it is caught in the EHB.",
            "   - When the victim needs it again, it loads in 40 cycles—matching a normal cache hit!"
        ],
        border_color=COLOR_ACCENT
    )
    add_card(
        s5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Buffer Structure & Properties",
        [
            "• Hardware Design: Small Content-Addressable Memory (CAM).",
            "• Fast Parallel Search: Checks all entries simultaneously.",
            "• Capacity: Typically 64 cache lines (only 4 KB of data).",
            "• Latency:",
            "   - Buffer Hit: 40 cycles (identical to cache hit).",
            "   - Normal Cache Hit: Untouched and 100% full speed.",
            "• Attacker View:",
            "   Access time stays flat. Attacker detects zero delay and learns no secrets."
        ]
    )
    set_speaker_notes(
        s5,
        "SPEAKER: Sreekar Tirumala | Round 1 | ~40s\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sripadha. On Slide 5, TreasureCache makes a very smart observation: kicking data out of the cache is not dangerous by itself. "
        "The danger only occurs when the victim has to wait 200 cycles for slow main memory. So instead of stopping evictions, TreasureCache simply hides them. "
        "It adds a small, fast hardware buffer called the Eviction-Holding Buffer, or EHB, right next to the cache. When victim data gets kicked out of the cache, "
        "it is caught and held in this buffer. If the victim needs that data again, it loads from the buffer in 40 cycles—exactly like a normal cache hit. "
        "The attacker sees flat access times and learns nothing.'"
    )

    # =============================================================
    # SLIDE 6: DUAL INSERTION RULES (Sreekar Tirumala)
    # =============================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_LIGHT_BG)
    add_header(s6, "Buffer Insertion Rules & Fixed-Time Flush", 
               "Paper Methodology: Dual Insertion Rules", "[Round 1 | Sreekar Tirumala - CS23I1034]")
    
    add_card(
        s6, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Rule 1 & Rule 2 for Saving Data",
        [
            "• Rule 1 (Victim Cache Eviction):",
            "   - Saves victim data that is pushed out of the cache by an attacker.",
            "   - Protects against Flush+Reload and Evict+Time.",
            "• Rule 2 (Reload Replacement):",
            "   - When victim pulls data back from the buffer into the cache, that incoming block pushes an existing line out.",
            "   - Rule 2 saves this second displaced block.",
            "   - Why Rule 2 is Required: Stops advanced Prime+Reprime+Probe attacks from detecting reload delays."
        ]
    )
    add_card(
        s6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Core Quotas & Fixed-Time Flush",
        [
            "• Domain Quotas:",
            "   - Each CPU core gets an equal slice of buffer space (N / D).",
            "   - Core 1 cannot overwrite data owned exclusively by Core 0.",
            "• Fixed-Time Flush (70 Clock Cycles):",
            "   - Flushing cached data normally takes 95 cycles; uncached data takes 45 cycles.",
            "   - TreasureCache forces all flush commands to take exactly 70 cycles.",
            "   - Completely stops Flush+Flush attacks."
        ]
    )
    set_speaker_notes(
        s6,
        "SPEAKER: Sreekar Tirumala | Round 1 | ~40s\n"
        "WHAT TO SAY:\n"
        "'Slide 6 shows how the buffer decides what data to store. Rule 1 saves victim data that gets pushed out of the cache by an attacker. "
        "But Rule 1 alone is not enough. When a victim loads data back from the buffer into the cache, that incoming block pushes an existing line out. "
        "Rule 2 catches this second displaced block. As we will prove later, Rule 2 is strictly required to stop advanced attacks. "
        "Finally, to stop flush attacks, TreasureCache forces all memory flush commands to take exactly 70 clock cycles, completely removing any timing differences.'"
    )

    # =============================================================
    # SLIDE 7: MATHEMATICAL VALIDATION (Sreekar Tirumala)
    # =============================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_LIGHT_BG)
    add_header(s7, "Mathematical Modeling & Security Bounds", 
               "Paper Analysis: Mathematical Validation", "[Round 1 | Sreekar Tirumala - CS23I1034]")
    
    add_card(
        s7, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Theoretical Security Boundary",
        [
            "• Eviction Probability Model:",
            "   Models how many cache lines an attacker must access to force data out.",
            "• The 89-Line Defense Threshold:",
            "   - At buffer capacity = 88 lines: Attacker success rate is under 50%.",
            "   - At capacity = 89 lines: First integer crossing 50% threshold.",
            "• 1,000x Attack Slowdown:",
            "   - Normal attack loop: ~10,000 clock cycles.",
            "   - With TreasureCache: Expands to nearly 10 million cycles.",
            "   - 1,000-fold slowdown makes real-time key extraction impossible."
        ]
    )
    add_card(
        s7, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "50,000-Trial Simulation Verification",
        [
            "• Python Monte Carlo Validation (`formal_verification.py`):",
            "   - Ran 50,000 random simulation trials.",
            "   - Theoretical vs. Empirical match: Less than 0.04% error.",
            "• Silicon Storage Overhead:",
            "   - 1 CPU Core: 0.44% cache area.",
            "   - 8 CPU Cores: 0.45% cache area.",
            "   - Storage cost stays strictly under 0.45% for any core count.",
            "• Venu will now evaluate hardware costs and paper limitations."
        ]
    )
    set_speaker_notes(
        s7,
        "SPEAKER: Sreekar Tirumala | Round 1 | ~40s\n"
        "WHAT TO SAY:\n"
        "'On Slide 7, we mathematically verified the paper's theoretical model. The paper proves that for an attacker to have even a 50% chance of evicting victim data, "
        "the buffer capacity must be at least 89 lines. This forces the attacker to expand their probing loop from 10,000 cycles to nearly 10 million cycles—a 1,000-times slowdown "
        "that makes practical attacks impossible. We ran a 50,000-trial random simulation in Python, and our results matched the mathematical model with less than 0.04% error. "
        "Now, Venu will cover hardware costs and the major flaw we discovered.'"
    )

    # =============================================================
    # SLIDE 8: HARDWARE FEASIBILITY (A Venu Vivek)
    # =============================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_LIGHT_BG)
    add_header(s8, "Hardware Feasibility & Silicon Costs", 
               "Paper Analysis: Hardware Feasibility", "[Round 1 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s8, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Is This Practical in Silicon Chips?",
        [
            "• Standard 28nm Chip Technology Evaluation:",
            "   - Total Buffer Complexity: 78,583 logic gates.",
            "   - Silicon Area: Only 0.057 mm².",
            "   - Occupies less than 0.34% of a 16MB cache footprint.",
            "• Fast Single-Cycle Search:",
            "   - Search Delay: 380 picoseconds.",
            "   - Fits easily inside a 2.5 GHz clock cycle (400 ps).",
            "   - Zero pipeline stalls or extra wait states."
        ]
    )
    add_card(
        s8, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Power & Filtering Efficiency",
        [
            "• Microarchitectural Traffic Filtering:",
            "   - Fast private L1 and L2 caches satisfy over 99% of memory requests.",
            "   - The EHB buffer is checked ONLY during rare cache misses and evictions.",
            "• Power Consumption:",
            "   - Consumes less than 2.2 milliwatts.",
            "   - Represents less than 0.03% of cache power budget.",
            "• Conclusion: Completely practical to build in real hardware."
        ]
    )
    set_speaker_notes(
        s8,
        "SPEAKER: A Venu Vivek | Round 1 | ~35s\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sreekar. On Slide 8, we evaluated whether this hardware can realistically be built in physical silicon chips. "
        "We modeled the design using 28-nanometer chip technology. The entire buffer takes only 78,583 logic gates, which is less than 0.34% of the cache silicon area. "
        "It searches for data in just 380 picoseconds, easily finishing in a single clock cycle at 2.5 GHz. Furthermore, because small private L1 and L2 caches handle 99% "
        "of requests, this buffer is rarely accessed, adding less than 0.03% to chip power. Hardware feasibility is fully confirmed.'"
    )

    # =============================================================
    # SLIDE 9: PAPER LIMITATIONS & GAPS (A Venu Vivek)
    # =============================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, COLOR_LIGHT_BG)
    add_header(s9, "The Critical Flaw in TreasureCache: Shared Memory", 
               "Paper Limitations: Critical Assessment", "[Round 1 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s9, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Flaw 1: Shared Memory Contention Collapse",
        [
            "• Real-World Setup: Cloud servers share code libraries (e.g., OpenSSL).",
            "• The Joint Ownership Problem:",
            "   - Shared lines are co-owned by both victim and attacker.",
            "   - TreasureCache checks ownership, but attacker counts as a co-owner!",
            "• The Complete Defense Failure:",
            "   - TreasureCache uses simple First-In-First-Out replacement.",
            "   - Attacker floods the buffer with shared memory requests.",
            "   - All victim secret lines get kicked out to slow RAM (0% retention, 201 cycles)!",
            "   - The side-channel attack is completely reopened!"
        ],
        border_color=COLOR_ALERT
    )
    add_card(
        s9, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Flaws 2 & 3: Wasted Space & Blind Thrashing",
        [
            "• Flaw 2: Rigid Cloud Quotas:",
            "   - Dividing space equally (N / D) locks capacity.",
            "   - Idle cores waste empty buffer lines while busy encryption tasks run out of room.",
            "• Flaw 3: Blindness to Attack Patterns:",
            "   - TreasureCache cannot tell normal programs apart from attack sweeps.",
            "• Our fix is presented on Slide 10."
        ],
        border_color=COLOR_ALERT
    )
    set_speaker_notes(
        s9,
        "SPEAKER: A Venu Vivek | Round 1 | ~40s\n"
        "WHAT TO SAY:\n"
        "'Slide 9 highlights the most important finding of our project. TreasureCache assumes CPU cores run completely separate programs. "
        "But in real-world cloud servers, virtual machines share common software libraries, like OpenSSL. These shared memory lines are co-owned by both victim and attacker. "
        "Because TreasureCache treats all data equally, an attacker can flood the buffer with shared requests and kick out all of the victim's secret keys to slow main memory! "
        "Victim protection collapses from 100% down to 0%, forcing slow 201-cycle delays that completely reopen the attack!'"
    )

    # =============================================================
    # SLIDE 10: PROPOSED UPGRADES (A Venu Vivek)
    # =============================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, COLOR_LIGHT_BG)
    add_header(s10, "Our Solution: Ada-EHB & Ada-EHB+ Upgrades", 
               "Our Proposed Solution: System Upgrade", "[Round 1 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s10, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Ada-EHB: Priority Retention Scoring",
        [
            "• The Core Fix: Give sensitive data a higher score.",
            "• Dynamic Retention Score R(k):",
            "   Calculates importance using sensitivity, access frequency, and age.",
            "• 'Sticky' Secret Lines:",
            "   - Encryption keys get top priority and become sticky.",
            "   - Attacker floods cannot displace them.",
            "   - Attacker churn is safely bypassed to RAM.",
            "• Result: Restores protection from 0% back to 100%!"
        ],
        border_color=COLOR_ACCENT
    )
    add_card(
        s10, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Ada-EHB+ (Ada-EHB 2.0): Cloud Upgrades",
        [
            "• Elastic Quotas (DEDQ):",
            "   Active programs dynamically borrow unused buffer lines from idle cores.",
            "• Instant Floor Return:",
            "   When an idle core wakes up, its reserved space is returned instantly.",
            "• Attack Sweep Detector:",
            "   Measures address randomness to automatically spot and penalize attack sweeps.",
            "• Sripadha will start Round 2 with our code and test results."
        ],
        border_color=COLOR_ACCENT
    )
    set_speaker_notes(
        s10,
        "SPEAKER: A Venu Vivek | Round 1 | ~40s\n"
        "WHAT TO SAY:\n"
        "'On Slide 10, to solve this problem, our team designed Ada-EHB and Ada-EHB+. In Ada-EHB, we created a Dynamic Retention Score. "
        "Sensitive cryptographic keys receive high scores and become sticky—an attacker cannot kick them out of the buffer. Incoming attacker floods are safely bypassed to RAM. "
        "In Ada-EHB+, active programs can dynamically borrow unused buffer space from idle cores, and an address entropy monitor automatically detects attack patterns. "
        "Now, Sripadha will start Round 2 with our code and benchmark results.'"
    )

    # =============================================================
    # SLIDE 11: SIMULATOR CODE (Kontham Sripadha)
    # =============================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, COLOR_LIGHT_BG)
    add_header(s11, "Simulator Design & Source Code Walkthrough", 
               "Project Implementation: Simulation Code", "[Round 2 | Kontham Sripadha - CS23I1018]")
    
    add_card(
        s11, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Cycle-Accurate Cache Simulator",
        [
            "• Complete Microarchitectural Model:",
            "   - Private L1 Caches: 32 KB per core (4 cycles).",
            "   - Private L2 Caches: 256 KB per core (14 cycles).",
            "   - Shared LLC Cache: 16 MB (40 cycles).",
            "   - Main Memory: 200 cycles minimum penalty.",
            "• Coherence Signaling:",
            "   Tracks back-invalidation messages between cores.",
            "• Rigorous Testing Protocol:",
            "   5 independent random seeds across 100 trials per setup."
        ]
    )
    add_code_card(
        s11, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Source Code & Design Choices",
        "simulation/cache_model.py",
        [
            "• `class TreasureCache` (Lines 112–220):",
            "   Implements buffer lookup pipeline, Rule 1 & Rule 2 checks, and domain quotas.",
            "• Design Choice: Fast Parallel Search:",
            "   Modeled as associative storage to check all tags simultaneously.",
            "• Design Choice: Message Piggybacking:",
            "   Coherence messages hitchhike on normal cache bus traffic without extra overhead.",
            "• `run_experiments.py`: Automates sweeps across buffer capacities (8..64 lines)."
        ]
    )
    set_speaker_notes(
        s11,
        "SPEAKER: Kontham Sripadha | Round 2 | ~35s\n"
        "WHAT TO SAY:\n"
        "'Welcome to Round 2. On Slide 11, I will walk you through our implementation. In simulation/cache_model.py, we built a cycle-accurate CPU cache simulator in Python. "
        "We accurately modeled private L1 and L2 caches, a 16MB shared cache, and off-chip RAM. In lines 112 to 220 of cache_model.py, we implemented the buffer logic, "
        "parallel tag matching, and insertion rules. In run_experiments.py, we automated tests across 5 independent random seeds and 100 trials to guarantee fair, repeatable results. "
        "Let us look at the observed results on Slide 12.'"
    )

    # =============================================================
    # SLIDE 12: RESULTS - ISOLATED RESIDENCY (Kontham Sripadha)
    # =============================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, COLOR_LIGHT_BG)
    add_header(s12, "Benchmark 1: Private Workload Retention", 
               "Experimental Results: Benchmark 1", "[Round 2 | Kontham Sripadha - CS23I1018]")
    
    fig1_path = os.path.join(sim_dir, "fig1_residency.png")
    if os.path.exists(fig1_path):
        s12.shapes.add_picture(fig1_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_card(
        s12, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Private Traffic Results (Figure 1)",
        [
            "• Workload: Victim and attacker use separate memory.",
            "• Unprotected Cache:",
            "   Victim loses all 8 data lines (0% retention, 202 cycles delay).",
            "• Buffer Capacity = 8 Lines (Quota = 4):",
            "   Both defenses retain exactly 4 lines, proving quota rules work.",
            "• Buffer Capacity >= 16 Lines:",
            "   Both TreasureCache and Ada-EHB achieve 100% retention (8/8 lines kept at 40 cycles).",
            "• Conclusion: In purely private workloads, TreasureCache works as promised."
        ]
    )
    set_speaker_notes(
        s12,
        "SPEAKER: Kontham Sripadha | Round 2 | ~35s\n"
        "WHAT TO SAY:\n"
        "'Slide 12 and Figure 1 show our first benchmark when programs do not share memory. In the unprotected baseline, the victim loses all 8 data lines, "
        "suffering 100% eviction to slow main memory. But with TreasureCache and our Ada-EHB, once buffer capacity reaches 16 lines or higher, all 8 victim lines "
        "are safely retained—achieving 100% protection at 40 cycles. This proves that under simple private workloads, TreasureCache works exactly as promised.'"
    )

    # =============================================================
    # SLIDE 13: RESULTS - EVICT+TIME LATENCY (Kontham Sripadha)
    # =============================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, COLOR_LIGHT_BG)
    add_header(s13, "Benchmark 2: Closing the Timing Leak", 
               "Experimental Results: Benchmark 2", "[Round 2 | Kontham Sripadha - CS23I1018]")
    
    fig2_path = os.path.join(sim_dir, "fig2_victim_latency.png")
    if os.path.exists(fig2_path):
        s13.shapes.add_picture(fig2_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_card(
        s13, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Timing Gap Neutralization (Figure 2)",
        [
            "• Unprotected Baseline Cache:",
            "   - Kicked-out line: 204.5 cycles (RAM fetch).",
            "   - Normal line: 40.0 cycles (Cache hit).",
            "   - Timing Gap: 164.5 cycles (Severe secret leakage).",
            "• With TreasureCache & Ada-EHB:",
            "   - Kicked-out line: 42.0 cycles (Buffer hit).",
            "   - Normal line: 40.0 cycles.",
            "   - Timing Gap: Only 2.0 cycles (98.8% reduction!).",
            "• Verdict: The 2-cycle difference is drowned out by chip noise. Sreekar will now present shared memory."
        ]
    )
    set_speaker_notes(
        s13,
        "SPEAKER: Kontham Sripadha | Round 2 | ~35s\n"
        "WHAT TO SAY:\n"
        "'Slide 13 and Figure 2 show access latency during an Evict+Time attack. In an unprotected cache, kicked-out data takes over 201 cycles to load, "
        "creating a massive 164.5-cycle timing gap that leaks secret keys. With TreasureCache and Ada-EHB, kicked-out data is served from the buffer in just 42 cycles. "
        "The timing gap drops from 164 cycles down to just 2 clock cycles. That tiny difference is completely hidden within normal hardware noise, neutralizing the attack. "
        "Now, Sreekar will present our shared-memory breakthrough.'"
    )

    # =============================================================
    # SLIDE 14: RESULTS - SHARED CONTENTION (Sreekar Tirumala)
    # =============================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, COLOR_LIGHT_BG)
    add_header(s14, "The Breakthrough: Fixing Shared-Memory Contention", 
               "Our Upgraded Results: Shared Memory", "[Round 2 | Sreekar Tirumala - CS23I1034]")
    
    fig3_path = os.path.join(sim_dir, "fig3_shared_contention.png")
    if os.path.exists(fig3_path):
        s14.shapes.add_picture(fig3_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_code_card(
        s14, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Shared Memory Results (Figure 3)",
        "simulation/ada_ehb_plus.py",
        [
            "• The Shared Memory Experiment:",
            "   Both programs share OpenSSL library code.",
            "• TreasureCache Collapses (Middle Bar):",
            "   - Retained: 0 out of 8 lines (0.0%).",
            "   - Delay: 201 cycles (DRAM miss penalty).",
            "• Ada-EHB Succeeds (Right Bar):",
            "   - Retained: 8 out of 8 lines (100.0%).",
            "   - Speed: 40 cycles (Buffer hit).",
            "• Source Code:",
            "   Lines 65–110 calculate the priority retention score, keeping secret lines safe."
        ]
    )
    set_speaker_notes(
        s14,
        "SPEAKER: Sreekar Tirumala | Round 2 | ~40s\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sripadha. Slide 14 and Figure 3 show the central experimental result of our project. Here, we tested shared libraries. "
        "Look at the middle bar on Figure 3: under shared attacker traffic, TreasureCache completely collapses to 0 out of 8 lines retained! "
        "The victim is forced to fetch from slow RAM at 201 cycles. Now look at our Ada-EHB on the right: it keeps all 8 lines safe at 40 cycles. "
        "In simulation/ada_ehb_plus.py, our retention score locks sensitive lines in place, completely solving the paper's biggest vulnerability.'"
    )

    # =============================================================
    # SLIDE 15: MULTI-VECTOR ATTACK BENCHMARK (Sreekar Tirumala)
    # =============================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, COLOR_LIGHT_BG)
    add_header(s15, "Multi-Vector Attack Suite Benchmark & Code", 
               "Project Implementation: Attack Suite", "[Round 2 | Sreekar Tirumala - CS23I1034]")
    
    fig4_path = os.path.join(sim_dir, "fig4_multi_vector_attacks.png")
    if os.path.exists(fig4_path):
        s15.shapes.add_picture(fig4_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_code_card(
        s15, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Attack Suite Code & Rule 2 Proof",
        "simulation/advanced_attacks.py",
        [
            "• 50 Rounds across 4 Attack Types (Figure 4):",
            "   - Flush+Reload: 164 cyc gap -> 2.0 cyc.",
            "   - Flush+Flush: 50 cyc gap -> 0.0 cyc (Fixed 70 cyc).",
            "   - Prime+Probe: 167 cyc gap -> 2.0 cyc.",
            "• Proving Rule 2 (Prime+Reprime+Probe):",
            "   - Defenses using Rule 1 only leak 168 cycles!",
            "   - Rule 2 catches displaced lines and closes the leak down to 2.0 cycles.",
            "   - Proves Rule 2 is strictly required."
        ]
    )
    set_speaker_notes(
        s15,
        "SPEAKER: Sreekar Tirumala | Round 2 | ~40s\n"
        "WHAT TO SAY:\n"
        "'On Slide 15 and Figure 4, we tested all 4 attack types across 50 rounds in simulation/advanced_attacks.py. Flush+Reload, Flush+Flush, and Prime+Probe "
        "are all reduced to a safe 2-cycle gap. Crucially, look at the fourth attack: Prime+Reprime+Probe. Defenses that only use Rule 1 leak 168 cycles! "
        "Our code proves that Rule 2 is strictly required to catch displaced lines and close the leak. Both TreasureCache and Ada-EHB pass this test.'"
    )

    # =============================================================
    # SLIDE 16: VERILOG RTL & SYNTHESIS (Sreekar Tirumala)
    # =============================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, COLOR_LIGHT_BG)
    add_header(s16, "Hardware Verilog RTL Implementation", 
               "Project Implementation: Verilog RTL", "[Round 2 | Sreekar Tirumala - CS23I1034]")
    
    fig5_path = os.path.join(sim_dir, "fig5_hardware_breakdown.png")
    if os.path.exists(fig5_path):
        s16.shapes.add_picture(fig5_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    
    add_code_card(
        s16, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4),
        "Synthesizable RTL Code (Figure 5)",
        "simulation/rtl/ (*.v)",
        [
            "• `cam_tag_cell.v`:",
            "   Single-cycle parallel search memory cell.",
            "• `retention_alu.v`:",
            "   Calculates priority scores using simple bit-shifts instead of expensive multipliers. Finishes in 4 cycles.",
            "• `token_bucket_limiter.v`:",
            "   Stops high-frequency eviction flood attacks.",
            "• Total Complexity: 78,583 gates. Adds less than 5% extra logic over basic TreasureCache. Over to Venu."
        ]
    )
    set_speaker_notes(
        s16,
        "SPEAKER: Sreekar Tirumala | Round 2 | ~40s\n"
        "WHAT TO SAY:\n"
        "'On Slide 16 and Figure 5, we wrote synthesizable Verilog code for the hardware in simulation/rtl/. We built the search cell in cam_tag_cell.v, "
        "a rate limiter in token_bucket_limiter.v, and the score calculator in retention_alu.v. To keep the hardware fast and simple, we used bit-shifts "
        "instead of expensive multipliers, finishing in just 4 clock cycles. The entire hardware requires 78,583 gates, adding less than 5% extra logic "
        "over basic TreasureCache. Now over to Venu for testing and conclusion.'"
    )

    # =============================================================
    # SLIDE 17: MASTER QA VERIFICATION (A Venu Vivek)
    # =============================================================
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17, COLOR_LIGHT_BG)
    add_header(s17, "Quality Assurance: 20/20 Tests Passing", 
               "Project Verification: Test Suite", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s17, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Automated Test Suite",
        [
            "• Test Suite File: `simulation/test_advanced_suite.py`.",
            "• Execution Speed: 20 tests run in just 0.04 seconds.",
            "• Pass Rate: 20 / 20 Tests Passed (100% Success).",
            "• What the Tests Verify:",
            "   - Tag searching and hit/miss reporting.",
            "   - Rule 1 and Rule 2 insertion correctness.",
            "   - Protection against all 4 attack types.",
            "   - Shared memory retention preservation.",
            "   - Hardware timing delay under 400 picoseconds."
        ]
    )
    add_code_card(
        s17, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Automated Code Checks",
        "simulation/test_advanced_suite.py",
        [
            "• `test_shared_contention_preservation`:",
            "   Checks that Ada-EHB keeps 100% of lines while TreasureCache drops to 0%.",
            "• `test_prp_condition2_defense`:",
            "   Checks that Rule 2 eliminates the 168-cycle leak.",
            "• `test_dedq_elastic_borrowing`:",
            "   Checks that active tasks can borrow idle lines and return them instantly with zero stalls.",
            "• Every claim in our report is proven by passing code."
        ]
    )
    set_speaker_notes(
        s17,
        "SPEAKER: A Venu Vivek | Round 2 | ~30s\n"
        "WHAT TO SAY:\n"
        "'Thank you, Sreekar. On Slide 17, to prove our code is robust, I built an automated test suite in simulation/test_advanced_suite.py. "
        "It runs 20 automated tests in just 0.04 seconds. It programmatically verifies tag matching, insertion rules, attack defenses, shared-memory protection, "
        "and hardware timing limits. All 20 tests pass with 100% success. Every claim we make is directly proven by code.'"
    )

    # =============================================================
    # SLIDE 18: COMPARATIVE ASSESSMENT (A Venu Vivek)
    # =============================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18, COLOR_LIGHT_BG)
    add_header(s18, "How Our Defense Compares to Prior Work", 
               "Architectural Assessment: Comparison", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    headers = ["Architecture", "Attack Protection", "Performance Loss", "Silicon Area", "Shared Memory Defended?"]
    rows = [
        ["Unprotected Baseline", "Vulnerable (164 cyc leak)", "0% (Fast)", "0.00%", "No (Vulnerable)"],
        ["PLCache (Partitioning)", "High (Isolated slices)", "Severe (-15% to -20%)", "1.20%", "Rigid (Wastes space)"],
        ["SHARP (Delay)", "Medium (Leaks in PRP)", "Low (<1%)", "0.20%", "No (Vulnerable)"],
        ["TreasureCache [1]", "High (Private only)", "Negligible (<0.5%)", "0.33%", "No (0% retention)"],
        ["Ada-EHB (Our Work)", "Complete (All 4 attacks)", "Negligible (<0.5%)", "0.34%", "YES (100% retention)"],
        ["Ada-EHB+ (Our Work)", "Complete + Adaptive", "Negligible (<0.5%)", "0.35%", "YES (100% retention)"]
    ]
    
    tbl_shape = s18.shapes.add_table(7, 5, Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(2.6)
    tbl.columns[1].width = Inches(2.5)
    tbl.columns[2].width = Inches(2.3)
    tbl.columns[3].width = Inches(1.8)
    tbl.columns[4].width = Inches(2.5)
    
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = "Calibri"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        
    for r_idx, r_data in enumerate(rows):
        bg = RGBColor(240, 248, 240) if "Our Work" in r_data[0] else (RGBColor(255, 255, 255) if r_idx % 2 == 0 else COLOR_LIGHT_BG)
        for c_idx, val in enumerate(r_data):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = "Calibri"
            p.font.size = Pt(10.5)
            p.font.color.rgb = COLOR_DARK_TEXT
            if "Our Work" in r_data[0]:
                p.font.bold = True
                
    set_speaker_notes(
        s18,
        "SPEAKER: A Venu Vivek | Round 2 | ~35s\n"
        "WHAT TO SAY:\n"
        "'Slide 18 compares our work against other defenses: Partitioning schemes like PLCache protect data, but slow down the CPU by up to 20%. "
        "Invalidation-delay schemes like SHARP are cheap, but leak secrets in multi-step attacks. TreasureCache is fast and secure for private data, "
        "but fails when memory is shared. Our Ada-EHB and Ada-EHB+ provide complete protection against all attacks, solve the shared memory problem, "
        "and adapt elastically to cloud workloads with virtually zero performance loss.'"
    )

    # =============================================================
    # SLIDE 19: TEAM ROLES & CONTRIBUTIONS (A Venu Vivek)
    # =============================================================
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19, COLOR_LIGHT_BG)
    add_header(s19, "Team Roles & Individual Contributions", 
               "Team Attribution: Work Division", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s19, Inches(0.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Kontham Sripadha\n(CS23I1018)\nLead Simulation Engineer",
        [
            "• Analyzed memory hierarchy timing gaps and prior defense failures.",
            "• Built the cycle-accurate Python cache simulator (`cache_model.py`).",
            "• Automated the 5-seed benchmark testing pipeline.",
            "• Generated publication charts for residency and access latency (Figures 1, 2, 3)."
        ],
        border_color=COLOR_PRIMARY
    )
    add_card(
        s19, Inches(4.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "Sreekar Tirumala\n(CS23I1034)\nLead Architectural Analyst",
        [
            "• Dissected buffer insertion rules and verified mathematical models.",
            "• Discovered the shared-memory contention flaw (`owners={0, 1}`).",
            "• Designed and implemented Ada-EHB and Ada-EHB+ (`ada_ehb_plus.py`).",
            "• Wrote the synthesizable Verilog hardware RTL code in `simulation/rtl/`."
        ],
        border_color=COLOR_SECONDARY
    )
    add_card(
        s19, Inches(8.8), Inches(1.5), Inches(3.65), Inches(5.4),
        "A Venu Vivek\n(CS23I1015)\nSecurity & Threat Specialist",
        [
            "• Evaluated hardware silicon costs and single-cycle timing feasibility.",
            "• Built the 4-vector attack suite in `advanced_attacks.py`.",
            "• Proved Rule 2 is required to stop Prime+Reprime+Probe attacks.",
            "• Created the 20-test automated verification suite (`test_advanced_suite.py`)."
        ],
        border_color=COLOR_ACCENT
    )
    set_speaker_notes(
        s19,
        "SPEAKER: A Venu Vivek | Round 2 | ~25s\n"
        "WHAT TO SAY:\n"
        "'On Slide 19, here is how our team divided the work: Kontham Sripadha led the memory timing analysis, built the Python cache simulator, "
        "and generated our benchmark charts. Sreekar Tirumala led the architectural design, discovered the shared-memory flaw, created Ada-EHB+, "
        "and wrote the synthesizable Verilog RTL. I, A Venu Vivek, evaluated silicon feasibility, built the multi-vector attack suite, and engineered "
        "the 20-test automated verification suite.'"
    )

    # =============================================================
    # SLIDE 20: CONCLUSION & REFERENCES (A Venu Vivek)
    # =============================================================
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_background(s20, COLOR_LIGHT_BG)
    add_header(s20, "Summary & Project Defense Q&A", 
               "Conclusion & Defense Q&A", "[Round 2 | A Venu Vivek - CS23I1015]")
    
    add_card(
        s20, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4),
        "Project Summary & Key Takeaways",
        [
            "• Main Conclusion: Hiding cache evictions in a tiny hardware buffer is far smarter than freezing cache partitions.",
            "• What We Discovered: Standard TreasureCache fails when programs share code libraries, dropping protection to 0%.",
            "• Our Upgrade: Ada-EHB and Ada-EHB+ restore 100% protection against all attacks with virtually zero performance loss.",
            "• Practical: Realizable in 78k gates, easily meeting single-cycle timing with negligible power draw."
        ],
        border_color=COLOR_ACCENT
    )
    add_card(
        s20, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4),
        "Open-Source Repository & Q&A",
        [
            "• Complete Reproducibility:",
            "   All simulation models, Verilog RTL, test scripts, and docs are available on GitHub:",
            "   `https://github.com/Sripadh16/IS-project.git`",
            "• Thank you for your time!",
            "• We now welcome your questions."
        ]
    )
    set_speaker_notes(
        s20,
        "SPEAKER: A Venu Vivek | Round 2 (Closing) | ~35s\n"
        "WHAT TO SAY:\n"
        "'To conclude on Slide 20: TreasureCache proves that hiding evictions in a tiny buffer is far better than freezing cache partitions. "
        "However, our project proved that basic TreasureCache fails under shared memory. Our extensions, Ada-EHB and Ada-EHB+, solve this flaw and provide 100% "
        "protection with negligible silicon overhead. All our code, tests, and documentation are open-sourced on GitHub. Thank you for your time, "
        "and we are now happy to answer your questions.'"
    )

    pptx_out_path = os.path.join(os.path.dirname(__file__), "TreasureCache_Presentation.pptx")
    prs.save(pptx_out_path)
    print(f"\n[Generated Presentation] {pptx_out_path}")
    return pptx_out_path


if __name__ == '__main__':
    generate_presentation()
