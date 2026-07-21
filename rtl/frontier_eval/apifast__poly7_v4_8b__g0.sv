module apifast__poly7_v4_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Stage 0 registers
    reg [15:0] p0;
    reg [15:0] x_reg0;

    // Stage 1 registers
    reg [15:0] p1;
    reg [15:0] x_reg1;

    // Stage 2 registers
    reg [15:0] p2;
    reg [15:0] x_reg2;

    // Stage 3 registers
    reg [15:0] p3;
    reg [15:0] x_reg3;

    // Stage 4 registers
    reg [15:0] p4;
    reg [15:0] x_reg4;

    // Stage 5 registers
    reg [15:0] p5;
    reg [15:0] x_reg5;

    // Stage 6 registers
    reg [15:0] p6;
    reg [15:0] x_reg6;

    // Stage 7 output register
    reg [15:0] y_next;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0      <= 16'd0;
            x_reg0  <= 16'd0;
            p1      <= 16'd0;
            x_reg1  <= 16'd0;
            p2      <= 16'd0;
            x_reg2  <= 16'd0;
            p3      <= 16'd0;
            x_reg3  <= 16'd0;
            p4      <= 16'd0;
            x_reg4  <= 16'd0;
            p5      <= 16'd0;
            x_reg5  <= 16'd0;
            p6      <= 16'd0;
            x_reg6  <= 16'd0;
            y       <= 16'd0;
        end else begin
            // Stage 0: start with c0 = 20
            p0      <= 16'd20;
            x_reg0  <= {8'd0, x};

            // Stage 1: p0 * x + c1
            p1      <= (p0 * x_reg0) + 16'd77;
            x_reg1  <= x_reg0;

            // Stage 2: p1 * x + c2
            p2      <= (p1 * x_reg1) + 16'd15;
            x_reg2  <= x_reg1;

            // Stage 3: p2 * x + c3
            p3      <= (p2 * x_reg2) + 16'd31;
            x_reg3  <= x_reg2;

            // Stage 4: p3 * x + c4
            p4      <= (p3 * x_reg3) + 16'd25;
            x_reg4  <= x_reg3;

            // Stage 5: p4 * x + c5
            p5      <= (p4 * x_reg4) + 16'd28;
            x_reg5  <= x_reg4;

            // Stage 6: p5 * x + c6
            p6      <= (p5 * x_reg5) + 16'd45;
            x_reg6  <= x_reg5;

            // Stage 7: p6 * x + c7
            y       <= (p6 * x_reg6) + 16'd10;
        end
    end

endmodule