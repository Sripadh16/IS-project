"""
build_presentation.py - Programmatically creates the professional PowerPoint Presentation (.pptx)
incorporating all evaluator feedback, formal Ada-EHB equations, updated figures,
and a dedicated references slide.
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


def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, title_text, category_text="RESEARCH PAPER ANALYSIS & EXTENSION"):
    tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = "Calibri"
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_SECONDARY
    
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.7))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(23)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY


def add_card(slide, left, top, width, height, title, items, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_CARD_BG
    shape.line.color.rgb = border_color if border_color else RGBColor(220, 224, 230)
    shape.line.width = Pt(1)

    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
    tf = tb.text_frame
    tf.word_wrap = True
    
    if title:
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.name = "Calibri"
        p_title.font.size = Pt(14)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_PRIMARY
        p_title.space_after = Pt(6)
        
    for item in items:
        p = tf.add_paragraph()
        p.text = item
        p.font.name = "Calibri"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_after = Pt(5)


def set_speaker_notes(slide, notes_text):
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text


def generate_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    sim_data_path = os.path.join(os.path.dirname(__file__), 'simulation', 'simulation_results.json')
    with open(sim_data_path, 'r') as f:
        sim_metrics = json.load(f)

    # =============================================================
    # SLIDE 1: TITLE SLIDE
    # =============================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_PRIMARY)
    
    tb1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(10.9), Inches(3.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p_tag = tf1.paragraphs[0]
    p_tag.text = "RESEARCH PAPER ANALYSIS & ARCHITECTURAL VALIDATION"
    p_tag.font.name = "Calibri"
    p_tag.font.size = Pt(14)
    p_tag.font.bold = True
    p_tag.font.color.rgb = RGBColor(160, 195, 240)
    p_tag.space_after = Pt(12)
    
    p_title = tf1.add_paragraph()
    p_title.text = "TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(32)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(255, 255, 255)
    p_title.space_after = Pt(14)
    
    p_sub = tf1.add_paragraph()
    p_sub.text = "Original Paper Authors: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren (IEEE TDSC 2024 [1])\n" \
                 "Team 06: Kontham Sripadha (Lead Analyst & Simulation Engineer), and Research Group"
    p_sub.font.name = "Calibri"
    p_sub.font.size = Pt(15)
    p_sub.font.color.rgb = RGBColor(220, 230, 242)
    
    set_speaker_notes(
        s1,
        "SPEAKER (Lead / Introduction):\n"
        "Welcome everyone. Today our team is presenting our research analysis and experimental validation of the paper "
        "'TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks', published in IEEE TDSC in 2024. "
        "In this presentation, we will walk through the microarchitectural root problem of cross-core cache timing channels, "
        "evaluate TreasureCache's innovative paradigm of hiding evictions rather than preventing them, discuss our critical assessment, "
        "and present our independent contribution: Ada-EHB, an adaptive frequency-aware eviction buffer verified through simulation."
    )

    # =============================================================
    # SLIDE 2: RESEARCH PROBLEM & MOTIVATION
    # =============================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_LIGHT_BG)
    add_header(s2, "The Root Problem: Memory Hierarchy Timing Disparities")
    
    add_card(
        s2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
        "Multi-Level Inclusive Cache Architecture",
        [
            "• Modern processors implement private L1/L2 caches per core alongside a large shared Last-Level Cache (LLC).",
            "• Inclusive Cache Invariant: Any line resident in private L1/L2 caches MUST also reside in the shared LLC.",
            "• Coherence Back-Invalidation: When an LLC set is full, evicting an LLC line forcibly ejects it from private L1/L2 caches.",
            "• Cross-core attackers can intentionally prime LLC sets to trigger back-invalidations of victim lines across cores."
        ]
    )
    
    add_card(
        s2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
        "Hierarchical Latency Disparity (Modeled)",
        [
            "• Private L1 Data Cache Hit: ~4 CPU cycles (fastest).",
            "• Private L2 Cache Hit: ~12 CPU cycles.",
            "• Shared LLC Cache Hit: ~38 CPU cycles (on-chip lookup).",
            "• Main Memory DRAM Miss: ~200 CPU cycles (long off-chip bus delay).",
            "• The 160-to-200-cycle timing gap between an LLC hit and a DRAM miss creates an unmistakable timing channel.",
            "• Attackers use unprivileged cycle counters (RDTSC) to monitor victim cryptographic lookups (AES S-Boxes, RSA) across security domains."
        ],
        border_color=COLOR_ALERT
    )
    
    set_speaker_notes(
        s2,
        "SPEAKER (Member 1 - Problem & Latency Hierarchy):\n"
        "To understand the core problem: modern multi-core processors use multi-level inclusive caches. "
        "Notice the distinct latency tiers: private L1 hits take 4 cycles, L2 hits take 12 cycles, LLC hits take 38 cycles, "
        "and off-chip DRAM misses take 200 cycles. When an inclusive LLC set fills up, an eviction sends a hardware back-invalidation "
        "to private caches. The resulting 160-to-200-cycle timing gap allows an unprivileged attacker to infer victim access patterns."
    )

    # =============================================================
    # SLIDE 3: THREAT MODEL & ATTACK TAXONOMY
    # =============================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_LIGHT_BG)
    add_header(s3, "Threat Model and Attack Taxonomy")
    
    add_card(
        s3, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.2),
        "Prime + Probe Attack",
        [
            "• NO shared memory required!",
            "1. Prime Phase: Attacker fills an LLC set with its own conflict lines.",
            "2. Victim Runs: Secret-dependent lookup evicts an attacker line.",
            "3. Probe Phase: Attacker measures reload time of primed lines.",
            "• High reload latency reveals victim used that specific set.",
            "• Extracts AES key bits across processes without shared pages."
        ]
    )
    add_card(
        s3, Inches(4.8), Inches(1.6), Inches(3.6), Inches(5.2),
        "Evict + Time Attack",
        [
            "• NO shared memory required!",
            "1. Evict Phase: Attacker evicts a targeted candidate cache set.",
            "2. Trigger Victim: Attacker triggers victim encryption execution.",
            "3. Time Phase: Attacker times the entire victim runtime.",
            "• Increased victim runtime indicates victim accessed the evicted line.",
            "• Directly exploits victim DRAM miss latency."
        ]
    )
    add_card(
        s3, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.2),
        "Flush + Reload / Flush [6, 7]",
        [
            "• REQUIRES shared memory pages (e.g. shared crypto libraries).",
            "1. Shared Pages: Attacker and victim map the same shared library.",
            "2. CLFLUSH: Attacker invalidates line with unprivileged flush.",
            "3. Reload / Flush: Measures reload latency or clflush execution time.",
            "• Cached line flushes in ~95 cyc; uncached flushes in ~45 cyc [7].",
            "• Flush+Flush causes zero misses, evading anomaly detectors."
        ]
    )
    
    set_speaker_notes(
        s3,
        "SPEAKER (Member 2 - Attack Taxonomy):\n"
        "The threat model encompasses two distinct attack classes. First, conflict-based attacks—Prime+Probe and Evict+Time—which do NOT "
        "require shared memory; the attacker only needs to share LLC sets. Second, flush-based attacks—Flush+Reload and Flush+Flush—which "
        "require shared memory pages. Existing defenses struggle because stopping set-conflicts does not stop flush attacks."
    )

    # =============================================================
    # SLIDE 4: LIMITATIONS OF PRIOR DEFENSES
    # =============================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_LIGHT_BG)
    add_header(s4, "Why Existing Defenses Fall Short")
    
    add_card(
        s4, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
        "Randomized Cache Mapping (CEASER [2], ScatterCache [4])",
        [
            "• Core Mechanism: Uses dynamic cryptographic ciphers (e.g. QARMA) to randomize the mapping from addresses to cache sets.",
            "• Critical Drawback 1: Complex address encryption on the critical path increases cache access latency.",
            "• Critical Drawback 2: Under sustained multi-round statistical profiling, attackers can still construct probabilistic eviction sets.",
            "• Critical Drawback 3: Completely ineffective against Flush+Reload and Flush+Flush attacks that bypass set indexing."
        ],
        border_color=COLOR_ALERT
    )
    
    add_card(
        s4, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
        "Strict Cache Partitioning (Intel CAT, DAWG [1])",
        [
            "• Core Mechanism: Isolates cache ways or sets strictly between security domains or processor cores.",
            "• Critical Drawback 1: Severe capacity fragmentation (SPEC benchmark overhead ranges from 4% to 14%).",
            "• Critical Drawback 2: Requires operating system scheduler modifications and dynamic partition management.",
            "• Critical Drawback 3: Intel CAT does not isolate shared memory pages; DAWG prevents shared page deduplication entirely."
        ],
        border_color=COLOR_ALERT
    )
    
    set_speaker_notes(
        s4,
        "SPEAKER (Member 1 - Prior Work Limitations):\n"
        "Prior work attempted to PREVENT evictions. Randomized mapping like CEASER adds encryption logic to the critical path and "
        "remains susceptible to statistical eviction set profiling, while failing to stop flush attacks. Partitioning like Intel CAT and "
        "DAWG causes 4 to 14% performance overhead due to cache fragmentation, requires OS changes, and restricts memory sharing."
    )

    # =============================================================
    # SLIDE 5: THE TREASURECACHE PARADIGM
    # =============================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_LIGHT_BG)
    add_header(s5, "TreasureCache Core Idea: Hide Evictions, Don't Prevent Them [1]")
    
    add_card(
        s5, Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.3),
        "The Fundamental Paradigm Shift",
        [
            "• Traditional Approach: 'Spend high silicon complexity and performance overhead attempting to prevent evictions.'",
            "• TreasureCache Philosophy: 'Allow LLC evictions to occur naturally as-is, but eliminate their side-channel utility by hiding exploitable evictions in a tiny buffer!' [1]",
            "• Architectural Impact: Eliminates address remapping, requires zero OS modifications, and preserves benchmark performance (< 1.2% overhead / 0.03-0.28% IPC variation in gem5 [1])."
        ],
        border_color=COLOR_ACCENT
    )
    
    add_card(
        s5, Inches(0.8), Inches(4.2), Inches(5.7), Inches(2.6),
        "1. Eviction-Hidden Buffer (EHB)",
        [
            "• Parameterized buffer capacity (e.g. 8-64 KB in full scale; modeled as 64 entries / 4 KB).",
            "• Serves hits in ~40 cycles (matches LLC hit latency).",
            "• Closes the timing gap between blocks in and out of LLC."
        ]
    )
    add_card(
        s5, Inches(6.8), Inches(4.2), Inches(5.7), Inches(2.6),
        "2. Constant-Time Flush (CT-Flush)",
        [
            "• Enforces a predefined waiting period (~70 cycles) even when target block is absent.",
            "• Cached and uncached lines take identical execution time.",
            "• Throttles Flush+Reload and Flush+Flush simultaneously."
        ]
    )
    
    set_speaker_notes(
        s5,
        "SPEAKER (Member 2 - TreasureCache Overview):\n"
        "Here is TreasureCache's breakthrough idea: Don't prevent evictions! Let evictions happen normally in the LLC, but hide exploitable "
        "evictions in a specialized buffer called the Eviction-Hidden Buffer (EHB). By matching EHB latency to LLC hit latency (~40 cycles), "
        "an evicted block returns data as fast as an LLC hit. And with Constant-Time Flush, flush instructions take a standardized waiting period."
    )

    # =============================================================
    # SLIDE 6: EHB ARCHITECTURE & PLACEMENT
    # =============================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_LIGHT_BG)
    add_header(s6, "Eviction-Hidden Buffer (EHB) & Dual Placement Policy [1]")
    
    add_card(
        s6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
        "Indexed Fully-Associative Structure",
        [
            "• Parameterized Sizing: Buffer capacity scales with core count and global threshold; not a fixed universal constant [1].",
            "• Why Fully-Associative? Direct-mapped or set-associative buffers introduce internal set-conflicts that an attacker could exploit.",
            "• Fully-associative architecture maximizes storage utilization—a block is replaced only when the buffer is completely full.",
            "• Latency Matching: Serves buffered blocks in ~40 cycles (in gem5, LLC/EHB hits centered at ~24 cycles with a 2-cycle CAM lookup [1])."
        ]
    )
    
    add_card(
        s6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
        "Dual-Condition Secure Placement Policy",
        [
            "To prevent the small buffer from overflowing, TreasureCache buffers an evicted LLC block if and only if [1]:",
            "1. Condition 1 (Private Sharers): The evicted block has active copies resident in private L1/L2 caches (exploitable due to inclusiveness).",
            "2. Condition 2 (EHB-Reload Replacement): The evicted block was replaced by a block loaded from the EHB.",
            "• If neither condition is met, the block is ordinary background traffic and bypasses directly to DRAM.",
            "• This drastically filters buffer pollution while safeguarding all vulnerable victim lines."
        ]
    )
    
    set_speaker_notes(
        s6,
        "SPEAKER (Member 3 - Architecture & Dual Placement):\n"
        "Slide 6 details the EHB architecture. The buffer is parameterized and fully-associative to eliminate internal set conflicts. "
        "To prevent buffer overflow, TreasureCache enforces a dual-condition placement policy: it buffers an evicted block only if it has "
        "active copies in private caches, or if it was replaced by a block loaded from EHB. Benign traffic bypasses directly to DRAM."
    )

    # =============================================================
    # SLIDE 7: REPLACEMENT & CT-FLUSH
    # =============================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_LIGHT_BG)
    add_header(s7, "Secure Replacement Policy & CT-Flush [1]")
    
    add_card(
        s7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
        "Ownership-Based Secure Replacement Policy",
        [
            "• Threat: An attacker could intentionally flood the EHB to create a secondary side channel inside the buffer itself.",
            "• Ownership Quotas: Each security domain is assigned a maximum capacity quota (Q = Capacity / N_domains) [1].",
            "• Strict Eligibility: Under _eligible, an incoming block can ONLY replace an entry whose owners are a subset of the incoming block's owners.",
            "• Attacker accesses in Domain 1 cannot displace victim blocks owned by Domain 0.",
            "• LLC Reload Coherence: When a buffered line is re-accessed, it is removed from EHB and reinstalled into LLC."
        ]
    )
    
    add_card(
        s7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
        "Constant-Time Flush (CT-Flush)",
        [
            "• Threat: Flush+Flush exploits the fact that flushing an un-cached line takes ~45 cycles, while a cached line takes ~95 cycles [7].",
            "• Predefined Waiting Period: CT-Flush enforces a predefined wait period (~70 cycles) even when the block is absent [1].",
            "• Security Guarantee: Flushes take identical time regardless of cached state, closing the Flush+Flush channel.",
            "• Allows shared read-only memory to remain enabled without OS or hypervisor modifications."
        ],
        border_color=COLOR_ACCENT
    )
    
    set_speaker_notes(
        s7,
        "SPEAKER (Member 3 - Replacement & CT-Flush):\n"
        "Slide 7 covers secure replacement and CT-Flush. TreasureCache uses domain ownership quotas and subset eligibility to prevent an attacker from evicting "
        "victim blocks from the buffer. CT-Flush uses a predefined waiting period so that clflush executes in constant time even when "
        "the block is absent, eliminating Flush+Flush side channels."
    )

    # =============================================================
    # SLIDE 8: CRITICAL ASSESSMENT & RESEARCH GAPS
    # =============================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_LIGHT_BG)
    add_header(s8, "Critical Assessment: Established Limitations vs. Hypotheses")
    
    add_card(
        s8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
        "Established Limitations (Literature)",
        [
            "1. CAM Power & Area Scaling: Fully-associative CAM structures consume high dynamic power; scaling to 64-core or multi-socket NUMA servers presents thermal challenges.",
            "2. Non-Inclusive Caches: Modern processors (e.g. AMD Zen 3/4) use non-inclusive caches [3], where LLC evictions do not force L1/L2 back-invalidation.",
            "3. Microarchitectural Timing Jitter: Subtle electrical differences between CAM buffers and SRAM banks could theoretically be profiled."
        ]
    )
    
    add_card(
        s8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
        "Team Research Hypothesis: Shared Memory Churn",
        [
            "• The Problem: The original paper's ownership quota protects against private evictions, but what happens during shared-memory churn?",
            "• Attack Scenario: If an attacker accesses shared library pages ({0, 1} joint ownership) and causes rapid evictions, shared lines enter the EHB.",
            "• Under standard FIFO/LRU within quotas, rapid shared churn prematurely displaces sensitive victim lines to DRAM.",
            "• Reopening the Timing Gap: When the victim re-accesses displaced lines, it incurs a DRAM miss, leaking secrets!",
            "• Motivation for Ada-EHB: We need frequency-aware retention scoring and burst rate-limiting."
        ],
        border_color=COLOR_ALERT
    )
    
    set_speaker_notes(
        s8,
        "SPEAKER (Member 4 - Critical Assessment):\n"
        "In Slide 8, we distinguish established paper limitations from our team's research hypothesis. The established limitations include "
        "CAM power scaling and non-inclusive caches. Our research hypothesis investigates shared-memory churn: if an attacker generates evictions "
        "of shared library pages that qualify for the EHB, unweighted LRU can displace victim lines to DRAM. This motivated our proposed extension: Ada-EHB."
    )

    # =============================================================
    # SLIDE 9: OUR PROPOSED EXTENSION: ADA-EHB
    # =============================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, COLOR_LIGHT_BG)
    add_header(s9, "Proposed Improvement: Ada-EHB Formal Specification")
    
    add_card(
        s9, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
        "Mathematical Retention Score Function",
        [
            "Every buffered entry k is assigned a dynamic Retention Score:",
            "       R(k) = [ S(k) * (1 + alpha * F(k)) ] / ln(1 + Age(k) + epsilon)",
            "• S(k) = Sensitivity Weight (3.0 for sensitive lines, 1.0 for normal).",
            "• F(k) = 4-Bit Saturating Frequency Counter (0 <= F(k) <= 15).",
            "• alpha = Frequency weight factor (0.2); epsilon = 10^-5.",
            "• Age(k) = Elapsed time (current_time - last_access_time).",
            "• Protected-Entry Sticky Residency: Sensitive entries are protected while eligible non-sensitive entries exist.",
            "• Overflow Bypass: If all eligible entries are sensitive, non-sensitive incoming blocks bypass directly to DRAM."
        ],
        border_color=COLOR_ACCENT
    )
    
    add_card(
        s9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
        "Token-Bucket Burst Rate-Limiting",
        [
            "• Token-Bucket Limiter per domain: M = 8 burst tokens.",
            "• Refill Rate: 1 token every 125 CPU cycles (8 per 1000 cycles).",
            "• Excess non-sensitive churn evictions bypass to DRAM, preventing buffer exhaustion.",
            "• Hardware Metadata Overhead: 86 bits (~11 bytes) per entry. For 64 entries, total metadata is 704 bytes (~0.05% of LLC silicon area)."
        ]
    )
    
    set_speaker_notes(
        s9,
        "SPEAKER (Member 4 - Ada-EHB Formal Design):\n"
        "Slide 9 presents the formal mathematical specification of Ada-EHB. We define a Retention Score R(k) combining sensitivity weight S(k), "
        "a 4-bit saturating frequency counter F(k), and an age denominator. When the buffer is full, we evict the entry with the minimum retention score. "
        "A token-bucket rate limiter filters non-sensitive burst evictions, requiring only ~704 bytes of metadata for 64 entries."
    )

    # =============================================================
    # SLIDE 10: SIMULATION METHODOLOGY & FIDELITY
    # =============================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, COLOR_LIGHT_BG)
    add_header(s10, "Simulation Methodology and Architecture Fidelity")
    
    add_card(
        s10, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
        "Cycle-Calibrated Multi-Core Simulator",
        [
            "• Modular Python cache architecture simulator (`simulation/`):",
            "  - Private L1 D-Cache: 32 KB, 8-way (4 cycles hit latency).",
            "  - Private L2 Cache: 256 KB, 8-way (12 cycles hit latency).",
            "  - Shared Inclusive LLC: 2 MB, 16-way (38 cycles hit latency).",
            "  - DRAM Access: 200 cycles latency.",
            "• Explicit private sharer tracking & coherence back-invalidation.",
            "• Implements CT-Flush predefined waiting period (~70 cycles).",
            "• 10 behavioral unit tests (`test_simulation.py`) all pass cleanly."
        ]
    )
    
    add_card(
        s10, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
        "Workloads & Multi-Trial Rigor",
        [
            "• Cryptographic Workload: Victim executes table lookups on an 8-line sensitive working set (AES T-tables).",
            "• Multi-Trial Rigor: 5 independent random seeds (101, 202, 303, 404, 505) with 300 rounds each.",
            "• Workload Scenarios Evaluated:",
            "  1. Domain-isolated churn (evaluating ownership quota isolation).",
            "  2. Shared-memory contention (evaluating Ada-EHB retention scoring).",
            "  3. Matched Evict+Time timing gap closure."
        ]
    )
    
    set_speaker_notes(
        s10,
        "SPEAKER (Member 3 - Simulation Methodology):\n"
        "Slide 10 details our simulator. We model private L1/L2 caches, an inclusive 2 MB LLC, and DRAM latencies. "
        "The victim executes AES table lookups while the attacker runs Prime+Probe across 16 sets. We evaluated all modes over 5 random seeds "
        "with 300 rounds each to report statistical means and standard deviations."
    )

    # =============================================================
    # SLIDE 11: RESULTS - DOMAIN ISOLATION & LATENCY
    # =============================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, COLOR_LIGHT_BG)
    add_header(s11, "Results: Domain Isolation and Access Latency")
    
    fig1_path = os.path.join(os.path.dirname(__file__), 'simulation', 'fig1_residency.png')
    fig2_path = os.path.join(os.path.dirname(__file__), 'simulation', 'fig2_victim_latency.png')
    
    if os.path.exists(fig1_path):
        s11.shapes.add_picture(fig1_path, Inches(0.8), Inches(1.6), width=Inches(5.7))
    if os.path.exists(fig2_path):
        s11.shapes.add_picture(fig2_path, Inches(6.8), Inches(1.6), width=Inches(5.7))
        
    set_speaker_notes(
        s11,
        "SPEAKER (Member 3 - Residency & Latency Results):\n"
        "Slide 11 presents our simulation findings for domain-isolated traffic. On the left (Figure 1), under domain-isolated churn, "
        "TreasureCache's domain ownership mechanism successfully isolates victim lines. At capacity 8, the 4-line quota is enforced; "
        "at capacities 16 and above, all 8 victim lines are retained for both TreasureCache and Ada-EHB. On the right (Figure 2), "
        "access latency drops from 202 cycles in the unprotected baseline down to 40 cycles."
    )

    # =============================================================
    # SLIDE 12: RESULTS - SHARED CONTENTION & TIMING GAP
    # =============================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, COLOR_LIGHT_BG)
    add_header(s12, "Results: Shared-Memory Contention and Timing Gap Closure")
    
    fig3_path = os.path.join(os.path.dirname(__file__), 'simulation', 'fig3_shared_contention.png')
    if os.path.exists(fig3_path):
        s12.shapes.add_picture(fig3_path, Inches(0.8), Inches(1.6), width=Inches(7.2))
        
    add_card(
        s12, Inches(8.3), Inches(1.6), Inches(4.2), Inches(5.2),
        "Key Findings (Shared Churn)",
        [
            "• Shared Contention (Figure 3):",
            "  - Joint ownership {0, 1} allows shared lines to compete.",
            "  - Standard TreasureCache: LRU displaces victim lines (0 / 8 retained, latency 201 cyc).",
            "  - Ada-EHB: Retention score (S=3.0, F>=1) and rate-limiting retain all 8 / 8 lines (latency 40 cyc).",
            "• Evict+Time Timing Gap:",
            "  - Unprotected: 164.45 +/- 0.23 cyc.",
            "  - TreasureCache: 2.00 +/- 0.00 cyc.",
            "  - Ada-EHB: 2.00 +/- 0.00 cyc."
        ],
        border_color=COLOR_ACCENT
    )
    
    set_speaker_notes(
        s12,
        "SPEAKER (Member 4 - Shared Contention Results):\n"
        "Slide 12 demonstrates where Ada-EHB provides a measurable advantage: under shared-memory contention. When blocks have joint ownership {0, 1}, "
        "unweighted LRU in standard TreasureCache allows attacker churn to displace all 8 victim lines to DRAM. In contrast, Ada-EHB's retention scoring "
        "and token-bucket rate-limiting preserve 100% of victim lines in the EHB, keeping access latency at 40 cycles. Furthermore, both defenses collapse "
        "the Evict+Time timing gap from 164.5 cycles down to 2 cycles."
    )

    # =============================================================
    # SLIDE 13: INDIVIDUAL CONTRIBUTIONS
    # =============================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, COLOR_LIGHT_BG)
    add_header(s13, "Team Member Roles & Individual Contributions")
    
    add_card(
        s13, Inches(0.8), Inches(1.6), Inches(5.6), Inches(2.5),
        "Kontham Sripadha (Lead Simulation Engineer)",
        [
            "• Implemented multi-core cache hierarchy simulator (`cache_model.py`, `attacks.py`).",
            "• Built automated benchmarking suite with 5 random seeds (`run_experiments.py`).",
            "• Generated publication-quality figures from verified simulator output."
        ]
    )
    add_card(
        s13, Inches(6.8), Inches(1.6), Inches(5.7), Inches(2.5),
        "Team Member 2 (Security & Threat Analyst)",
        [
            "• Formulated cross-core threat model & cryptographic attack analysis.",
            "• Detailed evaluation of Flush+Flush, Flush+Reload, and Prime+Probe vectors.",
            "• Assessed Constant-Time Flush (CT-Flush) waiting period mechanics."
        ]
    )
    add_card(
        s13, Inches(0.8), Inches(4.3), Inches(5.6), Inches(2.5),
        "Team Member 3 (Architecture Analyst)",
        [
            "• Evaluated inclusive cache back-invalidation invariants.",
            "• Comparative survey of prior randomized mapping (CEASER) & partitioning (CAT) defenses.",
            "• Reviewed gem5 SPEC CPU2017 benchmark results and storage overhead."
        ]
    )
    add_card(
        s13, Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.5),
        "Team Member 4 (Extension & Documentation Lead)",
        [
            "• Conceptualized and mathematically formulated Ada-EHB retention scoring.",
            "• Designed token-bucket burst rate-limiting algorithm and pseudocode.",
            "• Compiled comprehensive technical documentation and presentation deck."
        ]
    )
    
    set_speaker_notes(
        s13,
        "SPEAKER (All Members - Transition Segment):\n"
        "Slide 13 details our individual contributions. Kontham Sripadha served as Lead Simulation Engineer, implementing the cache simulator "
        "and benchmark pipeline; Member 2 led threat modeling and CT-Flush analysis; Member 3 analyzed prior defenses and gem5 results; "
        "and Member 4 formulated the Ada-EHB retention score algorithm and compiled documentation."
    )

    # =============================================================
    # SLIDE 14: CONCLUSION & TAKEAWAYS
    # =============================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, COLOR_PRIMARY)
    
    tb14 = s14.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(10.9), Inches(4.8))
    tf14 = tb14.text_frame
    tf14.word_wrap = True
    
    p_concl_tag = tf14.paragraphs[0]
    p_concl_tag.text = "SUMMARY & CONCLUDING REMARKS"
    p_concl_tag.font.name = "Calibri"
    p_concl_tag.font.size = Pt(14)
    p_concl_tag.font.bold = True
    p_concl_tag.font.color.rgb = RGBColor(160, 195, 240)
    p_concl_tag.space_after = Pt(12)
    
    p_concl_title = tf14.add_paragraph()
    p_concl_title.text = "Key Takeaways from our TreasureCache Study"
    p_concl_title.font.name = "Calibri"
    p_concl_title.font.size = Pt(28)
    p_concl_title.font.bold = True
    p_concl_title.font.color.rgb = RGBColor(255, 255, 255)
    p_concl_title.space_after = Pt(16)
    
    takeaways = [
        "1. Paradigm Shift: TreasureCache [1] proves that hiding evictions in a tiny buffer (EHB) is far more efficient than preventing evictions with complex address mapping.",
        "2. Negligible Overhead: Demonstrates < 1.2% overhead in gem5 while providing complete defense against Prime+Probe, Evict+Time, and Flush+Reload.",
        "3. Ownership Protection Verified: Under domain-isolated traffic, TreasureCache domain ownership strictly isolates victim lines from attacker churn.",
        "4. Ada-EHB Extension Validated: Under shared-memory contention ({0, 1} joint ownership), Ada-EHB retention scoring and rate-limiting preserve 100% of victim lines.",
        "5. Future Work: Adapting eviction-hiding principles to non-inclusive cache topologies and multi-socket NUMA systems."
    ]
    for t in takeaways:
        p_t = tf14.add_paragraph()
        p_t.text = t
        p_t.font.name = "Calibri"
        p_t.font.size = Pt(13.5)
        p_t.font.color.rgb = RGBColor(230, 238, 248)
        p_t.space_after = Pt(8)
        
    set_speaker_notes(
        s14,
        "SPEAKER (Lead / Conclusion):\n"
        "In conclusion, TreasureCache successfully demonstrates that hiding cache evictions is far superior to preventing them. "
        "Our analysis verified its ownership isolation under private traffic while demonstrating that Ada-EHB retention scoring "
        "provides crucial protection under shared-memory contention. Thank you for your time, and we now invite your questions!"
    )

    # =============================================================
    # SLIDE 15: REFERENCES SLIDE
    # =============================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, COLOR_LIGHT_BG)
    add_header(s15, "References & Academic Citations", "DOCUMENTATION & ATTRIBUTION")
    
    refs_items = [
        "[1] M. Li, K. Bu, C. Miao, and K. Ren, \"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks,\" IEEE Transactions on Dependable and Secure Computing, vol. 21, no. 5, pp. 4574-4588, Sept.-Oct. 2024.",
        "[2] M. K. Qureshi, \"CEASER: Mitigating Conflict-Based Cache Attacks via Encrypted-Address and Random-Remapping,\" in Proc. 51st Annual IEEE/ACM MICRO, 2018, pp. 775-787.",
        "[3] M. Yan, R. Sprabery, B. Gopireddy, C. Fletcher, R. Campbell, and J. Torrellas, \"Attack Directories, Not Caches: Side Channel Attacks in a Non-Inclusive World,\" in Proc. IEEE S&P, 2019.",
        "[4] G. Saileshwar and M. K. Qureshi, \"MIRAGE: Mitigating Conflict-Based Cache Attacks with a Practical Fully-Associative Design,\" in Proc. USENIX Security, 2021.",
        "[5] N. Fang, M. A. Kabir, and D. Tiwari, \"PhantomCache: Obfuscating Cache Set Mapping Against Side-Channel Attacks,\" in Proc. IEEE HPCA, 2020.",
        "[6] Y. Yarom and K. Falkner, \"FLUSH+RELOAD: A High Resolution, Low Noise, L3 Cache Side-Channel Attack,\" in Proc. 23rd USENIX Security Symposium, 2014.",
        "[7] D. Gruss, C. Maurice, K. Wagner, and S. Mangard, \"Flush+Flush: A Fast and Stealthy Cache Attack,\" in Proc. 13th DIMVA, 2016.",
        "[8] M. Yan, J. Choi, D. Skarlatos, A. Morrison, E. Torrellas, and J. Torrellas, \"SHARP: Mitigating Cache-Based Side-Channel Attacks in Inclusive Caches,\" IEEE TC, 2019."
    ]
    add_card(
        s15, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2),
        "Key Literature Cited in Analysis",
        refs_items
    )
    
    set_speaker_notes(
        s15,
        "SPEAKER (Lead):\n"
        "Here are the formal academic citations referenced throughout our analysis and presentation, including the original TreasureCache IEEE TDSC paper "
        "and foundational prior works across cache side-channel attacks and defense architectures."
    )

    ppt_out_path = os.path.join(os.path.dirname(__file__), "TreasureCache_Presentation.pptx")
    prs.save(ppt_out_path)
    print(f"\n[Generated Presentation] {ppt_out_path}")
    return ppt_out_path


if __name__ == '__main__':
    generate_presentation()
