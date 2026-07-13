module base__firr10__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

// Define parameters and local variables
parameter TAPS = 10;

reg [15:0] taps[TAPS-1:0];
reg [15:0] acc;
integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Reset all states to 0 on !rst_n
        y <= 0;
        for (i = 0; i < TAPS; i = i + 1) begin
            taps[i] <= 0;
        end
    end else begin
        // Shift old values in the delay line
        for (i = TAPS - 1; i > 0; i = i - 1) begin
            taps[i] <= taps[i - 1];
        end
        
        // Insert new value at the beginning of the delay line
        taps[0] <= x;
        
        // Compute the filtered output
        acc = 0;
        for (i = 0; i < TAPS; i = i + 1) begin
            acc = acc + taps[i] * (i + 1);
        end
        
        // Register the output
        y <= acc[15:0];
    end
end

endmodule