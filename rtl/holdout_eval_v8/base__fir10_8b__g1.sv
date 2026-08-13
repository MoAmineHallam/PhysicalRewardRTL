module base__fir10_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] sample_delay_0;
reg [7:0] sample_delay_1;
reg [7:0] sample_delay_2;
reg [7:0] sample_delay_3;
reg [7:0] sample_delay_4;
reg [7:0] sample_delay_5;
reg [7:0] sample_delay_6;
reg [7:0] sample_delay_7;
reg [7:0] sample_delay_8;
reg [7:0] sample_delay_9;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        sample_delay_0 <= 8'b0;
        sample_delay_1 <= 8'b0;
        sample_delay_2 <= 8'b0;
        sample_delay_3 <= 8'b0;
        sample_delay_4 <= 8'b0;
        sample_delay_5 <= 8'b0;
        sample_delay_6 <= 8'b0;
        sample_delay_7 <= 8'b0;
        sample_delay_8 <= 8'b0;
        sample_delay_9 <= 8'b0;
        y <= 16'b0;
    end else begin
        sample_delay_0 <= x;
        sample_delay_1 <= sample_delay_0;
        sample_delay_2 <= sample_delay_1;
        sample_delay_3 <= sample_delay_2;
        sample_delay_4 <= sample_delay_3;
        sample_delay_5 <= sample_delay_4;
        sample_delay_6 <= sample_delay_5;
        sample_delay_7 <= sample_delay_6;
        sample_delay_8 <= sample_delay_7;
        sample_delay_9 <= sample_delay_8;
        y <= {3'b0,sample_delay_0} * 3 + {5'b0,sample_delay_1} * 5 + {7'b0,sample_delay_2} * 7 
            + {9'b0,sample_delay_3} * 9 + {11'b0,sample_delay_4} * 11 + {11'b0,sample_delay_5} * 11
            + {9'b0,sample_delay_6} * 9 + {7'b0,sample_delay_7} * 7 + {5'b0,sample_delay_8} * 5 
            + {3'b0,sample_delay_9} * 3;
    end
end

endmodule