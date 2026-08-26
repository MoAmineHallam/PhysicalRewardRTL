module correctness_s1__poly16_v13_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((((((((((((((16'd45 * x + 16'd67) * x + 16'd56) * x + 16'd54) * x + 16'd26) * x + 16'd74) * x + 16'd47) * x + 16'd10) * x + 16'd96) * x + 16'd73) * x + 16'd22) * x + 16'd53) * x + 16'd23) * x + 16'd53) * x + 16'd77) * x + 16'd32) * x + 16'd61)))) & 16'hFFFF;
    end
endmodule
