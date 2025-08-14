import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

patch(FloorScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },


    async onClickTable(table) {
        const tableId = table.id;
        const pos = this.pos;
        const currentUserId = pos.user.id;

        // Fetch active orders on that table from backend
        const result = await this.orm.searchRead("pos.order", [
                ["table_id", "=", tableId],
                ["state", "=", "draft"]
            ])

        if (result.length > 0) {
            const orderOwnerId = result[0].user_id[0];
            if (orderOwnerId !== currentUserId) {
                await this.dialog.add(AlertDialog, {
                    title: _t('Access Denied'),
                    body: _t('This table already has an active order being handled by another user.'),
                });
                return;
            }
        }

        // Default behavior if no conflict
        return super.onClickTable(table);
    },
});
