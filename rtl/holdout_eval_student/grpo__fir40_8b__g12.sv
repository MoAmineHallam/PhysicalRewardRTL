module grpo__fir40_8b__g12 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0a, a1a, a2a, a3a, a4a, a5a, a6a, a7a, a8a, a9a, a10a, a11a, a12a, a13a, a14a, a15a, a16a, a17a, a18a, a19a, a20a, a21a, a22a, a23a, a24a, a25a, a26a, a27a, a28a, a29a, a30a, a31a, a32a, a33a, a34a, a35a, a36a, a37a, a38a, a39a;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0a <= 24'd0;
            a1a <= 24'd0;
            a2a <= 24'd0;
            a3a <= 24'd0;
            a4a <= 24'd0;
            a5a <= 24'd0;
            a6a <= 24'd0;
            a7a <= 24'd0;
            a8a <= 24'd0;
            a9a <= 24'd0;
            a10a <= 24'd0;
            a11a <= 24'd0;
            a12a <= 24'd0;
            a13a <= 24'd0;
            a14a <= 24'd0;
            a15a <= 24'd0;
            a16a <= 24'd0;
            a17a <= 24'd0;
            a18a <= 24'd0;
            a19a <= 24'd0;
            a20a <= 24'd0;
            a21a <= 24'd0;
            a22a <= 24'd0;
            a23a <= 24'd0;
            a24a <= 24'd0;
            a25a <= 24'd0;
            a26a <= 24'd0;
            a27a <= 24'd0;
            a28a <= 24'd0;
            a29a <= 24'd0;
            a30a <= 24'd0;
            a31a <= 24'd0;
            a32a <= 24'd0;
            a33a <= 24'd0;
            a34a <= 24'd0;
            a35a <= 24'd0;
            a36a <= 24'd0;
            a37a <= 24'd0;
            a38a <= 24'd0;
            a39a <= 24'd0;
            y <= 16'd0;
        end else begin
            a0a <= (8'd3 * x) + a1a;
            a1a <= (8'd5 * x) + a2a;
            a2a <= (8'd7 * x) + a3a;
            a3a <= (8'd9 * x) + a4a;
            a4a <= (8'd11 * x) + a5a;
            a5a <= (8'd13 * x) + a6a;
            a6a <= (8'd15 * x) + a7a;
            a7a <= (8'd17 * x) + a8a;
            a8a <= (8'd19 * x) + a9a;
            a9a <= (8'd21 * x) + a10a;
            a10a <= (8'd23 * x) + a11a;
            a11a <= (8'd25 * x) + a12a;
            a12a <= (8'd27 * x) + a13a;
            a13a <= (8'd29 * x) + a14a;
            a14a <= (8'd31 * x) + a15a;
            a15a <= (8'd33 * x) + a16a;
            a16a <= (8'd35 * x) + a17a;
            a17a <= (8'd37 * x) + a18a;
            a18a <= (8'd39 * x) + a19a;
            a19a <= (8'd41 * x) + a20a;
            a20a <= (8'd41 * x) + a21a;
            a21a <= (8'd39 * x) + a22a;
            a22a <= (8'd37 * x) + a23a;
            a23a <= (8'd35 * x) + a24a;
            a24a <= (8'd33 * x) + a25a;
            a25a <= (8'd31 * x) + a26a;
            a26a <= (8'd29 * x) + a27a;
            a27a <= (8'd27 * x) + a28a;
            a28a <= (8'd25 * x) + a29a;
            a29a <= (8'd23 * x) + a30a;
            a30a <= (8'd21 * x) + a31a;
            a31a <= (8'd19 * x) + a32a;
            a32a <= (8'd17 * x) + a33a;
            a33a <= (8'd15 * x) + a34a;
            a34a <= (8'd13 * x) + a35a;
            a35a <= (8'd11 * x) + a36a;
            a36a <= (8'd9 * x) + a37a;
            a37a <= (8'd7 * x) + a38a;
            a38a <= (8'd5 * x) + a39a;
            a39a <= (8'd3 * x);
            y <= a0a[15:0];
        end
    end
endmodule