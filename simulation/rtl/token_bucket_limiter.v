// ==============================================================================
// Module: token_bucket_limiter.v
// Description: Multi-Domain Hardware Token-Bucket Burst Rate-Limiting Controller
//              for the Ada-EHB Buffer.
// Parameters:
//   - NUM_DOMAINS: Number of isolated security domains (default: 4)
//   - BUCKET_CAPACITY: Burst tolerance M (default: 8 tokens)
//   - REFILL_CYCLES: Clock cycles per token refill (default: 125 cycles @ 2.5 GHz = 50 ns)
// Microarchitectural Invariant:
//   - Sensitive/cryptographic blocks (req_sensitive = 1) bypass rate-limiting with 0 delay.
//   - Non-sensitive blocks consume 1 token; if tokens == 0, block bypasses directly to DRAM.
// ==============================================================================

`timescale 1ns / 1ps

module token_bucket_limiter #(
    parameter NUM_DOMAINS     = 4,
    parameter DOMAIN_WIDTH    = 2,       // clog2(NUM_DOMAINS)
    parameter BUCKET_CAPACITY = 8,
    parameter REFILL_CYCLES   = 125      // 1 token / 125 cycles => 8 tokens / 1000 cycles
)(
    input  wire                      clk,
    input  wire                      rst_n,

    // Allocation Request Interface (from LLC Eviction Controller)
    input  wire                      req_valid,
    input  wire [DOMAIN_WIDTH-1:0]   req_domain,
    input  wire                      req_sensitive,

    // Grant / Bypass Decisions
    output reg                       grant,
    output reg                       bypass_to_dram,

    // Telemetry & Monitoring
    output wire [NUM_DOMAINS*4-1:0]  domain_token_counts
);

    // 7-bit Prescaler counter (counts 0 to REFILL_CYCLES - 1 = 124)
    reg [6:0] prescaler_cnt;
    wire      refill_tick = (prescaler_cnt == (REFILL_CYCLES - 1));

    // Per-domain 4-bit token registers
    reg [3:0] tokens [0:NUM_DOMAINS-1];

    // Status output packing
    genvar d;
    generate
        for (d = 0; d < NUM_DOMAINS; d = d + 1) begin : gen_status
            assign domain_token_counts[d*4 +: 4] = tokens[d];
        end
    endgenerate

    // Prescaler logic: Generates periodic refill pulse every 125 cycles
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prescaler_cnt <= 7'd0;
        end else if (refill_tick) begin
            prescaler_cnt <= 7'd0;
        end else begin
            prescaler_cnt <= prescaler_cnt + 1'b1;
        end
    end

    // Combinational Decision Logic
    always @(*) begin
        grant          = 1'b0;
        bypass_to_dram = 1'b0;

        if (req_valid) begin
            if (req_sensitive) begin
                // Legitimate sensitive line: unconditional admission, no token cost
                grant          = 1'b1;
                bypass_to_dram = 1'b0;
            end else begin
                // Non-sensitive line: inspect available domain tokens
                if (tokens[req_domain] > 4'd0) begin
                    grant          = 1'b1;
                    bypass_to_dram = 1'b0;
                end else begin
                    // Token exhausted: DoS/churn burst actively deflected to DRAM
                    grant          = 1'b0;
                    bypass_to_dram = 1'b1;
                end
            end
        end
    end

    // Token Registers Sequential Update & Refill Handling
    integer k;
    reg is_consuming;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (k = 0; k < NUM_DOMAINS; k = k + 1) begin
                tokens[k] <= BUCKET_CAPACITY[3:0]; // Initialized to full capacity
            end
        end else begin
            for (k = 0; k < NUM_DOMAINS; k = k + 1) begin
                is_consuming = req_valid && (!req_sensitive) && 
                               (req_domain == k[DOMAIN_WIDTH-1:0]) && 
                               (tokens[k] > 4'd0);

                if (refill_tick && !is_consuming) begin
                    // Pure refill
                    if (tokens[k] < BUCKET_CAPACITY[3:0]) begin
                        tokens[k] <= tokens[k] + 1'b1;
                    end
                end else if (refill_tick && is_consuming) begin
                    // Concurrent refill and consumption cancel out (net change = 0)
                    tokens[k] <= tokens[k];
                end else if (!refill_tick && is_consuming) begin
                    // Pure consumption
                    tokens[k] <= tokens[k] - 1'b1;
                end
            end
        end
    end

endmodule
