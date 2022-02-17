// SPDX-License-Identifier: MIT

pragma solidity ^0.8.4;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "./Mintable.sol";

contract HighriseLand is ERC721Enumerable, Mintable {
    constructor(
        string memory _name,
        string memory _symbol,
        address _imx
    ) ERC721(_name, _symbol) Mintable(msg.sender, _imx) {}

    function _mintFor(
        address user,
        uint256 tokenId,
        bytes memory blueprint
    ) internal override {
        _safeMint(user, tokenId, blueprint);
    }

    function _baseURI() internal view override returns (string memory) {
        return "s3://highrise-land/metadata/";
    }

    function tokensOfOwner(address owner)
        public
        view
        returns (uint256[] memory)
    {
        uint256 balance = balanceOf(owner);
        uint256[] memory tokens;

        for (uint256 i = 0; i < balance; i++) {
            tokens[i] = tokenOfOwnerByIndex(owner, i);
        }

        return tokens;
    }
}
