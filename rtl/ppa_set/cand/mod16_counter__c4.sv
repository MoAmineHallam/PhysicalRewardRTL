module mod16_counter__c4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

always @(posedge clk)
begin
    if (!rst_n) // active-low reset
        count <= 4'd0;
    else
        count <= (count == 4'd15) ? 4'd0 : count + 1;
end

endmodule