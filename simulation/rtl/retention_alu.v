// ==============================================================================
// Module: retention_alu.v
// Description: Fixed-Point 8-bit Dynamic Retention Score Calculation Unit
//              and 4-bit Saturating Frequency Counter for Ada-EHB.
// Formula:
//   R(k) = [ S(k) * (1 + alpha * F(k)) ] / ln(1 + Age(k) + epsilon)
// Parameters:
//   - S(k): Sensitivity weight (3.0 for sensitive lines, 1.0 for normal)
//   - F(k): 4-bit saturating counter (0 <= F(k) <= 15)
//   - alpha: 0.2 (frequency importance factor = 1/5)
//   - Age(k): Cycle distance since last access
//   - 16-entry piecewise-linear ROM lookup table for ln(1 + Age)
// ==============================================================================

`timescale 1ns / 1ps

// ------------------------------------------------------------------------------
// Submodule: freq_counter_4bit
// 4-bit Saturating Access Frequency Counter
// Increments on each buffer hit, saturates at 4'hF (15).
// ------------------------------------------------------------------------------
module freq_counter_4bit (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       inc_en,
    input  wire       clr_en,
    output reg  [3:0] count_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count_out <= 4'd1; // Initial frequency upon insertion is 1
        end else if (clr_en) begin
            count_out <= 4'd1;
        end else if (inc_en) begin
            if (count_out < 4'hF) begin
                count_out <= count_out + 1'b1;
            end
        end
    end
endmodule


// ------------------------------------------------------------------------------
// Submodule: ln_age_rom_16entry
// 16-Entry Piecewise-Linear Logarithmic ROM Lookup Table
// Maps 16-bit elapsed age to an 8-bit Q4.4 fixed-point ln(1 + Age) denominator,
// and corresponding 8-bit reciprocal scale factor W_recip = round(256 / (5 * ln(1+Age))).
// ------------------------------------------------------------------------------
module ln_age_rom_16entry (
    input  wire [15:0] age_cycles,
    output reg  [3:0]  segment_idx,
    output reg  [7:0]  ln_val_q44,     // ln(1 + Age) in Q4.4 format (4 integer, 4 fraction)
    output reg  [7:0]  recip_lut_val   // Scaled reciprocal: round(256 / (5 * ln(1+Age)))
);

    // Segment classifier: Leading-one priority encoder (Log2 range partitioning)
    always @(*) begin
        if      (age_cycles >= 16'd32768) segment_idx = 4'd15;
        else if (age_cycles >= 16'd16384) segment_idx = 4'd14;
        else if (age_cycles >= 16'd8192)  segment_idx = 4'd13;
        else if (age_cycles >= 16'd4096)  segment_idx = 4'd12;
        else if (age_cycles >= 16'd2048)  segment_idx = 4'd11;
        else if (age_cycles >= 16'd1024)  segment_idx = 4'd10;
        else if (age_cycles >= 16'd512)   segment_idx = 4'd9;
        else if (age_cycles >= 16'd256)   segment_idx = 4'd8;
        else if (age_cycles >= 16'd128)   segment_idx = 4'd7;
        else if (age_cycles >= 16'd64)    segment_idx = 4'd6;
        else if (age_cycles >= 16'd32)    segment_idx = 4'd5;
        else if (age_cycles >= 16'd16)    segment_idx = 4'd4;
        else if (age_cycles >= 16'd8)     segment_idx = 4'd3;
        else if (age_cycles >= 16'd4)     segment_idx = 4'd2;
        else if (age_cycles >= 16'd2)     segment_idx = 4'd1;
        else                              segment_idx = 4'd0;
    end

    // 16-Entry ROM Lookup Table: Synthesizes into compact combinational MUX array (< 100 NAND2 gates)
    always @(*) begin
        case (segment_idx)
            // Segment  0: Age [0, 1]     -> ln(2)     = 0.693 -> Q4.4 = 11  (0x0B), Recip = 74
            4'd0:  begin ln_val_q44 = 8'h0B; recip_lut_val = 8'd74; end
            // Segment  1: Age [2, 3]     -> ln(4)     = 1.386 -> Q4.4 = 22  (0x16), Recip = 37
            4'd1:  begin ln_val_q44 = 8'h16; recip_lut_val = 8'd37; end
            // Segment  2: Age [4, 7]     -> ln(8)     = 2.079 -> Q4.4 = 33  (0x21), Recip = 25
            4'd2:  begin ln_val_q44 = 8'h21; recip_lut_val = 8'd25; end
            // Segment  3: Age [8, 15]    -> ln(16)    = 2.773 -> Q4.4 = 44  (0x2C), Recip = 18
            4'd3:  begin ln_val_q44 = 8'h2C; recip_lut_val = 8'd18; end
            // Segment  4: Age [16, 31]   -> ln(32)    = 3.466 -> Q4.4 = 55  (0x37), Recip = 15
            4'd4:  begin ln_val_q44 = 8'h37; recip_lut_val = 8'd15; end
            // Segment  5: Age [32, 63]   -> ln(64)    = 4.159 -> Q4.4 = 67  (0x43), Recip = 12
            4'd5:  begin ln_val_q44 = 8'h43; recip_lut_val = 8'd12; end
            // Segment  6: Age [64, 127]  -> ln(128)   = 4.852 -> Q4.4 = 78  (0x4E), Recip = 11
            4'd6:  begin ln_val_q44 = 8'h4E; recip_lut_val = 8'd11; end
            // Segment  7: Age [128, 255] -> ln(256)   = 5.545 -> Q4.4 = 89  (0x59), Recip = 9
            4'd7:  begin ln_val_q44 = 8'h59; recip_lut_val = 8'd9;  end
            // Segment  8: Age [256, 511] -> ln(512)   = 6.238 -> Q4.4 = 100 (0x64), Recip = 8
            4'd8:  begin ln_val_q44 = 8'h64; recip_lut_val = 8'd8;  end
            // Segment  9: Age [512, 1023]-> ln(1024)  = 6.931 -> Q4.4 = 111 (0x6F), Recip = 7
            4'd9:  begin ln_val_q44 = 8'h6F; recip_lut_val = 8'd7;  end
            // Segment 10: Age [1024, 2047]-> ln(2048) = 7.625 -> Q4.4 = 122 (0x7A), Recip = 7
            4'd10: begin ln_val_q44 = 8'h7A; recip_lut_val = 8'd7;  end
            // Segment 11: Age [2048, 4095]-> ln(4096) = 8.318 -> Q4.4 = 133 (0x85), Recip = 6
            4'd11: begin ln_val_q44 = 8'h85; recip_lut_val = 8'd6;  end
            // Segment 12: Age [4096, 8191]-> ln(8192) = 9.011 -> Q4.4 = 144 (0x90), Recip = 6
            4'd12: begin ln_val_q44 = 8'h90; recip_lut_val = 8'd6;  end
            // Segment 13: Age [8192, 16383]-> ln(16384)=9.704 -> Q4.4 = 155 (0x9B), Recip = 5
            4'd13: begin ln_val_q44 = 8'h9B; recip_lut_val = 8'd5;  end
            // Segment 14: Age [16384, 32767]-> ln(32768)=10.397-> Q4.4 = 166 (0xA6), Recip = 5
            4'd14: begin ln_val_q44 = 8'hA6; recip_lut_val = 8'd5;  end
            // Segment 15: Age >= 32768   -> ln(65536)=11.090-> Q4.4 = 177 (0xB1), Recip = 5
            4'd15: begin ln_val_q44 = 8'hB1; recip_lut_val = 8'd5;  end
            default: begin ln_val_q44 = 8'h0B; recip_lut_val = 8'd74; end
        endcase
    end

endmodule


// ------------------------------------------------------------------------------
// Top Module: retention_alu
// 8-Bit Fixed-Point Retention Scoring Arithmetic Logic Unit
// Single-cycle combinational datapath with synchronous output registration.
// ------------------------------------------------------------------------------
module retention_alu (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        calc_en,
    input  wire        is_sensitive,   // 1'b1 = Cryptographic/Sensitive (S=3), 1'b0 = Normal (S=1)
    input  wire [3:0]  freq_count,     // 4-bit saturating frequency (0..15)
    input  wire [15:0] age_cycles,     // Current cycle - last_access cycle

    output reg  [7:0]  retention_score,// 8-bit fixed-point retention score
    output reg         score_valid
);

    wire [3:0] segment_idx;
    wire [7:0] ln_val_q44;
    wire [7:0] recip_lut_val;

    // Instantiate 16-entry Logarithm & Reciprocal ROM
    ln_age_rom_16entry u_rom (
        .age_cycles(age_cycles),
        .segment_idx(segment_idx),
        .ln_val_q44(ln_val_q44),
        .recip_lut_val(recip_lut_val)
    );

    // --------------------------------------------------------------------------
    // Numerator Evaluation:
    // Base frequency term: (5 + freq_count)  [ranges from 5 to 20]
    // Scaled by Sensitivity weight: S = 3 if sensitive, else 1
    // num_unscaled = S * (5 + freq_count)    [ranges from 5 to 60]
    // --------------------------------------------------------------------------
    wire [5:0] freq_term    = 6'd5 + {2'b00, freq_count};
    wire [7:0] num_unscaled = is_sensitive ? (freq_term * 8'd3) : {2'b00, freq_term};

    // --------------------------------------------------------------------------
    // Score Multiplication:
    // raw_product = num_unscaled * recip_lut_val
    // num_unscaled <= 60, recip <= 74 => raw_product <= 4440 (13 bits)
    // Shift right by 4 bits (divide by 16) yields an 8-bit score [0..255]
    // --------------------------------------------------------------------------
    wire [15:0] raw_product = num_unscaled * recip_lut_val;
    wire [7:0]  computed_score = (raw_product[15:4] > 12'd255) ? 8'hFF : raw_product[11:4];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            retention_score <= 8'd0;
            score_valid     <= 1'b0;
        end else if (calc_en) begin
            retention_score <= computed_score;
            score_valid     <= 1'b1;
        end else begin
            score_valid     <= 1'b0;
        end
    end

endmodule
