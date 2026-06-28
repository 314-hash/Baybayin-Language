// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "hardhat/console.sol";

contract Pagbati {
    string public mensahe = "Kamusta mula sa BBL!";
    address public tagapamahala;
    uint256 public bilang_ng_pagbabago = 0;

    constructor(address unang_alamat) {
        tagapamahala = unang_alamat;
    }

    function kuninMensahe() public view returns (string memory) {
        return mensahe;
    }

    function baguhinMensahe(string memory bagong_mensahe) public {
        if ((keccak256(bytes(mensahe)) != keccak256(bytes(bagong_mensahe)))) {
            mensahe = bagong_mensahe;
            bilang_ng_pagbabago = (bilang_ng_pagbabago + 1);
            console.log(("Nabagong mensahe sa: " + bagong_mensahe));
        }
    }
}

contract Main {
    function run() public {
        console.log("Nagsisimula ang programa...");
        Pagbati demo = new Pagbati("0x1234567890123456789012345678901234567890");
        string memory kasalukuyang_mensahe = demo.kuninMensahe();
        console.log(kasalukuyang_mensahe);
        demo.baguhinMensahe("Bagong Mensahe 2026");
        console.log(("Bilang ng pagbabago: " + demo.bilang_ng_pagbabago));
    }
}