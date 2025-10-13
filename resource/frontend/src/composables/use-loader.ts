import { Loading } from "quasar";
export function useLoader(msg?: string) {
    function show() {
        Loading.show({
            message: msg ?? "Loading data..",
            boxClass: "bg-grey-2 text-grey-9",
            spinnerColor: "primary",
        });
    }
    function hide() {
        Loading.hide();
    }
    return {
        show,
        hide,
    };
}
