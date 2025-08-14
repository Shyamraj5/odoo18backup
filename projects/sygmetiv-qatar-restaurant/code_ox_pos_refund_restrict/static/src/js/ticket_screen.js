import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
    async onDoRefund() {
        const self = this;
        var cashier = this.pos.get_cashier()
        if (self.pos.config.restrict_refund && cashier._role != 'manager') {
            await this.dialog.add(AlertDialog, {
                title: _t('Access Denied'),
                body: _t('You have no permission to Refund. Plaese contact Manager'),
            });
            return;
        }
        await super.onDoRefund(...arguments);
    },
});
