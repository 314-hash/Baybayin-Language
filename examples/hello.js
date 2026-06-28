class Pagbati {
    mensahe = 'Kamusta mula sa BBL!';
    tagapamahala = null;
    bilang_ng_pagbabago = 0;

    constructor(unang_alamat) {
        this.tagapamahala = unang_alamat;
    }

    kuninMensahe() {
        return this.mensahe;
    }

    baguhinMensahe(bagong_mensahe) {
        if ((this.mensahe !== bagong_mensahe)) {
            this.mensahe = bagong_mensahe;
            this.bilang_ng_pagbabago = (this.bilang_ng_pagbabago + 1);
            console.log(('Nabagong mensahe sa: ' + bagong_mensahe));
        }
    }
}

console.log('Nagsisimula ang programa...');

let demo = new Pagbati('0x1234567890123456789012345678901234567890');

let kasalukuyang_mensahe = demo.kuninMensahe();

console.log(kasalukuyang_mensahe);

demo.baguhinMensahe('Bagong Mensahe 2026');

console.log(('Bilang ng pagbabago: ' + demo.bilang_ng_pagbabago));