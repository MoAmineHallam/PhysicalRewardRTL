`timescale 1ns/1ps
// Instantiates all 7 golden-reference DUTs with counter-driven inputs.
// sel[2:0] (from la_axi SEL register) picks which DUT feeds probe[15:0].
//
// Probe packing per sel value:
//   0 edge_detector : {14'b0, cnt[8], rise}
//   1 alu_mux       : {12'b0, result[3:0]}
//   2 comb_always   : {12'b0, valid, out[2:0]}
//   3 bcd_counter   : {8'b0,  tens[3:0], ones[3:0]}
//   4 bit_manip     : {4'b0,  reversed[7:0], popcount[3:0]}
//   5 dff_array     : {8'b0,  q[7:0]}
//   6 shift_reg     : {8'b0,  q[7:0]}
module dut_top (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [2:0] sel,
    output reg [15:0] probe
);
    // free-running counter — deterministic stimulus source
    reg [31:0] cnt;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) cnt <= 32'b0;
        else        cnt <= cnt + 1'b1;

    // --- 0: edge_detector ---
    wire ed_rise;
    edge_detector u_ed (
        .clk(clk), .rst_n(rst_n),
        .in(cnt[8]),
        .rise(ed_rise)
    );

    // --- 1: alu_mux ---
    wire [3:0] alu_result;
    alu_mux u_alu (
        .clk(clk), .rst_n(rst_n),
        .a(cnt[3:0]), .b(cnt[7:4]), .op(cnt[10:8]),
        .result(alu_result)
    );

    // --- 2: comb_always (priority encoder) ---
    wire [2:0] pe_out;
    wire       pe_valid;
    comb_always u_pe (
        .clk(clk), .rst_n(rst_n),
        .in(cnt[7:0]),
        .out(pe_out), .valid(pe_valid)
    );

    // --- 3: bcd_counter ---
    wire [3:0] bcd_ones, bcd_tens;
    bcd_counter u_bcd (
        .clk(clk), .rst_n(rst_n),
        .en(1'b1),
        .ones(bcd_ones), .tens(bcd_tens)
    );

    // --- 4: bit_manip ---
    wire [7:0] bm_rev;
    wire [3:0] bm_pop;
    bit_manip u_bm (
        .clk(clk), .rst_n(rst_n),
        .in(cnt[7:0]),
        .reversed(bm_rev), .popcount(bm_pop)
    );

    // --- 5: dff_array ---
    wire [7:0] dff_q;
    dff_array u_dff (
        .clk(clk), .rst_n(rst_n),
        .en(cnt[0]), .d(cnt[8:1]),
        .q(dff_q)
    );

    // --- 6: shift_reg ---
    wire [7:0] sr_q;
    shift_reg u_sr (
        .clk(clk), .rst_n(rst_n),
        .en(1'b1), .sin(cnt[0]),
        .q(sr_q)
    );

    always @(*) begin
        case (sel)
            3'd0: probe = {14'b0,      cnt[8],  ed_rise};
            3'd1: probe = {12'b0,               alu_result};
            3'd2: probe = {12'b0,      pe_valid, pe_out};
            3'd3: probe = {8'b0,       bcd_tens, bcd_ones};
            3'd4: probe = {4'b0,       bm_rev,   bm_pop};
            3'd5: probe = {8'b0,                 dff_q};
            3'd6: probe = {8'b0,                 sr_q};
            default: probe = 16'b0;
        endcase
    end
endmodule
