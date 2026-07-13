module base__firr18__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Define the number of taps
    parameter TAPS = 18;

    // Internal register for the output
    reg [31:0] output_reg;

    // Shift register for the delay line
    reg [7:0] tap [0:TAPS-1];

    // Combinational logic to calculate the output based on the delay line
    always @(*) begin
        output_reg = 0;
        for (int i = 0; i < TAPS; i = i + 1) begin
            output_reg = output_reg + ((i + 1) * tap[i]);
        end
        output_reg = output_reg & 32'hFFFF; // Ensure only the lower 16 bits are used
    end

    // Always block for clock edge operations
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all internal registers to zero
            output_reg <= 0;
            foreach (tap[i]) begin
                tap[i] <= 0;
            end
        end else begin
            // Shift new sample into delay line
            for (int i = TAPS - 1; i > 0; i = i - 1) begin
                tap[i] <= tap[i - 1];
            end
            tap[0] <= x;
            // Update the output register on the positive edge of the clock
            y <= output_reg[15:0];
        end
    end

endmodule