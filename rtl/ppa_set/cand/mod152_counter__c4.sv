module mod152_counter__c4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

    always @(posedge clk, negedge rst_n)
    begin
        if (!rst_n) // synchronous active-low reset
            count <= 8'd0;
        else // free-running counter
            if (count == 8'd151)
                count <= 8'd0;
            else
                count <= count + 1;
    end

endmodule