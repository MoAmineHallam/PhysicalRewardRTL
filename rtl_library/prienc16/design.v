// 16-to-4 priority encoder (registered). MSB highest priority.
module prienc16 (
    input  wire clk, rst_n,
    input  wire [15:0] req,
    output reg  [3:0] enc,
    output reg  valid
);
    always @(posedge clk) begin
        if (!rst_n) begin enc<=0; valid<=0; end
        else begin
            valid <= |req;
            if (req[15]) enc <= 4'd15;
            else if (req[14]) enc <= 4'd14;
            else if (req[13]) enc <= 4'd13;
            else if (req[12]) enc <= 4'd12;
            else if (req[11]) enc <= 4'd11;
            else if (req[10]) enc <= 4'd10;
            else if (req[9]) enc <= 4'd9;
            else if (req[8]) enc <= 4'd8;
            else if (req[7]) enc <= 4'd7;
            else if (req[6]) enc <= 4'd6;
            else if (req[5]) enc <= 4'd5;
            else if (req[4]) enc <= 4'd4;
            else if (req[3]) enc <= 4'd3;
            else if (req[2]) enc <= 4'd2;
            else if (req[1]) enc <= 4'd1;
            else enc <= 4'd0;
        end
    end
endmodule
