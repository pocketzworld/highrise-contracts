// SPDX-License-Identifier: MIT

pragma solidity ^0.8.4;

interface IHighriseLandV3 {
    function mint(address user, uint256 tokenId) external;
    function bindToEstate(address owner, uint256[] memory tokenIds) external;
}