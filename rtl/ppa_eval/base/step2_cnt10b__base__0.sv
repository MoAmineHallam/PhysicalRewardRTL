module step2_cnt10b__base__0 (
    input  wire clk, rst_n,
    output reg  [9:0] count
);

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 10'd0;
        end else begin
            count <= count + 10'd2;
        end
    end
    
endmodule