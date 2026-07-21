module apifast__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Pipeline registers - maximum frequency optimization
    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5;
    reg [15:0] p0, p1, p2, p3, p4, p5;
    reg [15:0] s0, s1, s2, s3, s4;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            tap0 <= 8'd0;
            tap1 <= 8'd0;
            tap2 <= 8'd0;
            tap3 <= 8'd0;
            tap4 <= 8'd0;
            tap5 <= 8'd0;
            p0 <= 16'd0;
            p1 <= 16'd0;
            p2 <= 16'd0;
            p3 <= 16'd0;
            p4 <= 16'd0;
            p5 <= 16'd0;
            s0 <= 16'd0;
            s1 <= 16'd0;
            s2 <= 16'd0;
            s3 <= 16'd0;
            s4 <= 16'd0;
            y  <= 16'd0;
        end else begin
            // Delay line shift (tap0 = newest = current x)
            tap5 <= tap4;
            tap4 <= tap3;
            tap3 <= tap2;
            tap2 <= tap1;
            tap1 <= tap0;
            tap0 <= x;

            // Pipeline stage 1: Multiplications (coefficient = k+1)
            p0 <= {8'd0, tap0} * 16'd1;  // 1*tap0
            p1 <= {8'd0, tap1} * 16'd2;  // 2*tap1
            p2 <= {8'd0, tap2} * 16'd3;  // 3*tap2
            p3 <= {8'd0, tap3} * 16'd4;  // 4*tap3
            p4 <= {8'd0, tap4} * 16'd5;  // 5*tap4
            p5 <= {8'd0, tap5} * 16'd6;  // 6*tap5

            // Pipeline stage 2: First level additions
            s0 <= p0 + p1;
            s1 <= p2 + p3;
            s2 <= p4 + p5;

            // Pipeline stage 3: Second level additions
            s3 <= s0 + s1;
            s4 <= s2;

            // Pipeline stage 4: Final addition and output
            // Sum = s3 + s4 = p0+p1+p2+p3 + p4+p5
            y <= s3 + s4;
        end
    end

endmodule