class Pagbati:
    mensahe: str = 'Kamusta mula sa BBL!'
    tagapamahala: str = None
    bilang_ng_pagbabago: int = 0

    def __init__(self, unang_alamat: str):
        self.tagapamahala = unang_alamat

    def kuninMensahe(self) -> str:
        return self.mensahe

    def baguhinMensahe(self, bagong_mensahe: str) -> None:
        if (self.mensahe != bagong_mensahe):
            self.mensahe = bagong_mensahe
            self.bilang_ng_pagbabago = (self.bilang_ng_pagbabago + 1)
            print(('Nabagong mensahe sa: ' + str(bagong_mensahe)))

print('Nagsisimula ang programa...')

demo = Pagbati('0x1234567890123456789012345678901234567890')

kasalukuyang_mensahe: str = demo.kuninMensahe()

print(kasalukuyang_mensahe)

demo.baguhinMensahe('Bagong Mensahe 2026')

print(('Bilang ng pagbabago: ' + str(demo.bilang_ng_pagbabago)))