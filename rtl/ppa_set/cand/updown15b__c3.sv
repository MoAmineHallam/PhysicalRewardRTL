module updown15b__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [14:0] count
);

    always @(posedge clk, negedge rst_n)
    begin
        if (!rst_n)
            count <= 15'b0;
        else
            count <= (dir) ? count - 15'd1 : count + 15'd1;
    end

endmodule