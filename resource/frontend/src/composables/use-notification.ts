import { Notify } from "quasar";

export function useNotification(type: "positive" | "negative", msg: string) {
    if (type === "positive") {
        Notify.create({
            type: "positive",
            message: msg,
            position: "top",
            color: "positive-alert",
            textColor: "positive-alert",
            icon: "check",
            iconSize: "sm",
            classes:
                "bs-warning success bs-font-medium-1-semi-bold bs-alert-notification",
            actions: [
                {
                    icon: "close",
                    color: "positive-alert",
                    round: false,
                    padding: "0px",
                    size: "sm",
                },
            ],
        });
    } else {
        Notify.create({
            type: "negative",
            message: msg,
            position: "top",
            color: "negative-alert",
            textColor: "negative-alert",
            icon: "mdi-close-circle-outline",
            iconSize: "sm",
            classes:
                "bs-warning error bs-font-medium-1-semi-bold bs-alert-notification",
            actions: [
                {
                    icon: "close",
                    color: "negative-alert",
                    round: false,
                    padding: "0px",
                    size: "sm",
                },
            ],
        });
    }
}
