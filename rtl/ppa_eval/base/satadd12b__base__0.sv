module satadd12b__base__0 (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);

reg [11:0] adder_out;
wire [11:0] max_val = 12'hfff;
wire overflow = (adder_out > max_val);

// ripple-carry adder
always @ (posedge clk) begin
    if (rst_n == 0) begin
        adder_out <= 0;
    end else begin
        adder_out <= a + b;
    end
end

// comparator
always @ (posedge clk) begin
    if (rst_n == 0) begin
        sum <= 0;
    end else begin
        if (overflow) begin
            sum <= max_val;
        end else begin
            sum <= adder_out;
        end
    end
end

endmodule