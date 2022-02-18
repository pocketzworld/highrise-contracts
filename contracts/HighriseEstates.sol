// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./HighriseLand.sol";

contract HighriseEstates is ERC721Enumerable, IERC721Receiver {
    using Counters for Counters.Counter;

    address public land;
    Counters.Counter private _tokenIds;
    mapping(uint256 => uint256[]) public parcelsToEstates;

    constructor(
        string memory _name,
        string memory _symbol,
        address _land
    ) ERC721(_name, _symbol) {
        land = _land;
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

    function mintFromParcels(uint256[] memory tokenIds)
        public
        returns (uint256)
    {
        Land(land).bindToEstate(msg.sender, tokenIds);
        _tokenIds.increment();
        uint256 tokenId = _tokenIds.current();
        parcelsToEstates[tokenId] = tokenIds;
        _mint(msg.sender, tokenId);
        return tokenId;
    }

    function burn(uint256 tokenId) public {
        _burn(tokenId);
    }

    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) public returns (bytes4) {
        return IERC721Receiver.onERC721Received.selector;
    }
}
