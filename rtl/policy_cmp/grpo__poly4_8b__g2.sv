module grpo__poly4_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] r0;
    reg [15:0] r1;
    reg [15:0] r2;
    reg [15:0] r3;
    reg [15:0] r4;
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    // Delay the input: same value, but earlier in the pipeline, so the
    // combinational path from the input to the output is shorter.
    always @(posedge clk) begin
        xd1 <= x;
        xd2 <= xd1;
        xd3 <= xd2;
        xd4 <= xd3;
    end
    // The registers that form the pipeline: one per stage of the
    // degree-4 Horner polynomial, in the order of the polynomial (the
    // longers stages are the ones that the combinational path first
    // traverses).
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 16'd0;
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
        end else begin
            r0 <= 16'd1;
            r1 <= r0 * xd1 + 16'd3;
            r2 <= r1 * xd2 + 16'd5;
            r3 <= r2 * xd3 + 16'd7;
            r4 <= r3 * xd4 + 16'd9;
        end
    end
    // Output the last register.
    always @(posedge clk) begin
        y <= r4;
    end
endmodule