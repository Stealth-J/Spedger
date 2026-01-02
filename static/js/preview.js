let removeSelectionObj;
let saveChangesBtn = find('.save_changes_btn');
saveChangesBtn.disabled = true;

class RemoveSelection{
    constructor(previewHolder){
        this.removedIds = [];
        this.hiddenInput = find('#editSlipDetails input');

        let typingElem = document.createElement('div');
        let dot = document.createElement('span');
        typingElem.classList.add('typing');
        typingElem.append(dot, dot.cloneNode(), dot.cloneNode())
        this.typingElem = typingElem;

        let currentThis = this;
        finds('.remove_selection_btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                currentThis.removeSelectionDisplay.apply(currentThis, [btn]);
            })
        })
    }
    removeSelectionDisplay(btn){
        let game = btn.closest('.game');
        if (!game || finds('.game').length === 1) return;

        game.classList.add('remove_game');
        setTimeout(() => {
            game.remove();
            this.updatePreviewHeader();
        }, 300)
        this.updateRemovedIds(btn);
        saveChangesBtn.disabled = false;
    }
    updateRemovedIds(btn){
        let game = btn.closest('.game');
        let gameId = game.id.replace('game', '');
        this.removedIds.push(gameId);
        this.hiddenInput.value = this.removedIds.join(',');
    }
    updatePreviewHeader(){
        let previewHeader = document.getElementById('previewHeader');
        let spanElem = find('.preview_code_group', previewHeader);
        let pElem = find('.preview_extra_info', previewHeader);
        let gamesLeft = finds('.game').length;
        let oddsLeft = finds('.game .odds').map((elem) => +elem.textContent).reduce(
            (res, odds) => res * odds 
        );
        oddsLeft = +oddsLeft.toFixed(1);

        spanElem.innerHTML = '';
        spanElem.append(this.typingElem);
        pElem.innerHTML = `${gamesLeft}(${oddsLeft})`;
    }
}

function initRemoveSelection(){
    let previewHolder = find('.preview_main');
    removeSelectionObj = new RemoveSelection(previewHolder);
}
initRemoveSelection()

bdy.addEventListener('preview_success', () => {
    initRemoveSelection();
    saveChangesBtn.disabled = true;
});