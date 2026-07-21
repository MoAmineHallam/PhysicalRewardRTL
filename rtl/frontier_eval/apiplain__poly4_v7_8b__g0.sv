module apiplain__poly4_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Horner's method for polynomial: 24*x^4 + 36*x^3 + 17*x^2 + 21*x + 50
    // Evaluated as: ((((24)*x + 36)*x + 17)*x + 21)*x + 50
    
    wire [15:0] stage0, stage1, stage2, stage3;
    
    // Stage 0: start with c4 = 24 (highest coefficient)
    assign stage0 = 8'd24;
    
    // Stage 1: stage0 * x + c3 = 24*x + 36
    assign stage1 = (stage0 * x) + 16'd36;
    
    // Stage 2: stage1 * x + c2 = (24*x + 36)*x + 17
    assign stage2 = (stage1 * x) + 16'd17;
    
    // Stage 3: stage2 * x + c1 = ((24*x + 36)*x + 17)*x + 21
    assign stage3 = (stage2 * x) + 16'd21;
    
    // Stage 4: stage3 * x + c0 = (((24*x + 36)*x + 17)*x + 21)*x + 50
    // Keep only low 16 bits
    wire [15:0] result;
    assign result = (stage3 * x) + 16'd50;
    
    // Registered output with active-low reset
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= result;
        end
    end

endmodule