module base__poly4_v7_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Coefficients of the polynomial in c0 first order
    localparam [15:0] C0 = 16'd24;
    localparam [15:0] C1 = 16'd36;
    localparam [15:0] C2 = 16'd17;
    localparam [15:0] C3 = 16'd21;
    localparam [15:0] C4 = 16'd50;

    // Internal registers for Horner's method
    reg  [15:0] y_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear output on reset
            y <= 16'b0;
        end else begin
            // Horner's method evaluation
            y_reg <= ((C4 + x * (C3 + x * (C2 + x * (C1 + x * C0))))) % 65536;
            y <= y_reg;
        end
    end

endmodule