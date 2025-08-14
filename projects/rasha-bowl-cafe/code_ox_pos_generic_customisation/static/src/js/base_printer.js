/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { htmlToCanvas } from "@point_of_sale/app/printer/render_service";
import { rpc } from "@web/core/network/rpc";

patch(BasePrinter.prototype, {
    setup() {
        super.setup(...arguments);
    },

    async printReceipt(receipt) {
        if (receipt) {
            console.log(receipt.outerHTML);
            this.receiptQueue.push(receipt);
        }
        let image, printResult;
        while (this.receiptQueue.length > 0) {
            receipt = this.receiptQueue.shift();
            const htmlData = await rpc("/pos/parse_data",{
                    data: receipt.outerHTML,
                });
            const flask_url = await rpc("/pos/flask_url",{});
            image = this.processCanvas(
                await htmlToCanvas(receipt, { addClass: "pos-receipt-print" })
            );
            try {
                // printResult = await this.sendPrintingJob(image);
                printResult = await fetch(flask_url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({'content': htmlData.data})
                });
            } catch {
                // Error in communicating to the IoT box.
                this.receiptQueue.length = 0;
                return this.getActionError();
            }
            // rpc call is okay but printing failed because
            // IoT box can't find a printer.
            if (!printResult || printResult.result === false) {
                this.receiptQueue.length = 0;
                return this.getResultsError(printResult);
            }
        }
        return { successful: true };
    }
})