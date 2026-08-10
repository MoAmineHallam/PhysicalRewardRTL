module base__fir6_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] sample_delay [0:5];

    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            y <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                sample_delay[i] <= 0;
            end
        end else begin
            sample_delay[0] <= x;
            for (int i = 0; i < 5; i = i + 1) begin
                sample_delay[i+1] <= sample_delay[i];
            end

            y <= {8'd0, x} * 8'd3 + {1'b0, sample_delay[0]} * 8'd5 + {3'd0, sample_delay[1]} * 8'd7 + {4'd0, sample_delay[2]} * 8'd7 + {1'b0, sample_delay[3]} * 8'd5 + {1'b0, sample_delay[4]} * 8'd3;
        end
    end

endmodule