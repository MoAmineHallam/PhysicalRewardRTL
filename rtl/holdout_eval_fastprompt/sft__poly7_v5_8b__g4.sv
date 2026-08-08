module sft__poly7_v5_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [15:0] t0;
    reg  [15:0] t1;
    reg  [15:0] t2;
    reg  [15:0] t3;
    reg  [15:0] t4;
    reg  [15:0] t5;
    reg  [15:0] t6;
    reg  [15:0] t7;
    always @(posedge clk) begin
        if (!rst_n) begin y <= 16'd0; t0 <= 16'd0; t1 <= 16'd0; t2 <= 16'd0; t3 <= 16'd0; t4 <= 16'd0; t5 <= 16'd0; t6 <= 16'd0; t7 <= 16'd0; end
        else begin
            y <= ((((((((16'd53 * x + 16'd68) * x + 16'd36) * x + 16'd67) * x + 16'd8) * x + 16'd1) * x + 16'd93) * x + 16'd82));
            t0 <= 16'd53 * x;
            t1 <= t0 + 16'd68;
            t2 <= t1 + 16'd36;
            t3 <= t2 + 16'd67;
            t4 <= t3 + 16'd8;
            t5 <= t4 + 16'd1;
            t6 <= t5 + 16'd93;
            t7 <= t6 + 16'd82;
        end
    end
endmodule