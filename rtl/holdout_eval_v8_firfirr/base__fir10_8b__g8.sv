module base__fir10_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] sample_mem [0:9];  // 10-element delay line
integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        for (i = 0; i < 10; i = i + 1) begin
            sample_mem[i] <= 0;
        end
    end
    else begin
        y <= {3'b0, x} * 8'd3
            + {3'b0, sample_mem[0]} * 8'd5
            + {3'b0, sample_mem[1]} * 8'd7
            + {3'b0, sample_mem[2]} * 8'd9
            + {3'b0, sample_mem[3]} * 8'd11
            + {3'b0, sample_mem[4]} * 8'd11
            + {3'b0, sample_mem[5]} * 8'd9
            + {3'b0, sample_mem[6]} * 8'd7
            + {3'b0, sample_mem[7]} * 8'd5
            + {3'b0, sample_mem[8]} * 8'd3;
        for (i = 9; i > 0; i = i - 1) begin
            sample_mem[i] <= sample_mem[i-1];
        end
        sample_mem[0] <= x;
    end
end

endmodule