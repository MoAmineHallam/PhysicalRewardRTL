module step2_cnt12b__base__1 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk)
begin
    if (!rst_n) // active-low reset
        count <= 0;
    else
        count <= count + 2; // increment by 2 each cycle
end

endmodule