// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin-upgradeable/contracts/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721RoyaltyUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/utils/ERC721HolderUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165Checker.sol";

import "../../interfaces/IHighriseLand.sol";
import "../opensea/Utils.sol";
import "../opensea/ContextMixin.sol";

function parseToCoordinates(uint256 tokenId) pure returns (uint256[2] memory) {
    return [tokenId >> 24, tokenId & 0xFFFFFF];
}

contract HighriseEstate is
    Initializable,
    ERC721Upgradeable,
    ERC721EnumerableUpgradeable,
    ERC721HolderUpgradeable,
    ERC721RoyaltyUpgradeable,
    OwnableUpgradeable,
    ContextMixin
{
    using ERC165Checker for address;
    using Counters for Counters.Counter;

    // ------------------------ STORAGE --------------------------------------
    string private _baseTokenURI;
    address private _land;
    Counters.Counter private _tokenIds;
    mapping(uint256 => uint256[]) public estatesToParcels;
    address private _openseaRegistryAddress;

    // -----------------------------------------------------------------------

    // ------------------------ INITIALIZER -----------------------------------
    function initialize(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address land,
        address openseaRegistryAddress
    ) public virtual initializer {
        require(
            land.supportsInterface(type(IHighriseLand).interfaceId),
            "IS_NOT_HIGHRISE_LAND_CONTRACT"
        );
        require(
            land.supportsInterface(type(IERC721).interfaceId),
            "IS_NOT_ERC721_CONTRACT"
        );
        __HighriseEstate_init(
            name,
            symbol,
            baseTokenURI,
            land,
            openseaRegistryAddress
        );
    }

    function __HighriseEstate_init(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        address land,
        address openseaRegistryAddress
    ) internal onlyInitializing {
        __ERC721_init(name, symbol);
        __ERC721Enumerable_init();
        __ERC721Holder_init();
        __Ownable_init();
        __HighriseEstate_init_unchained(
            name,
            symbol,
            baseTokenURI,
            land,
            openseaRegistryAddress
        );
    }

    function __HighriseEstate_init_unchained(
        string memory,
        string memory,
        string memory baseTokenURI,
        address land,
        address openseaRegistryAddress
    ) internal onlyInitializing {
        _baseTokenURI = baseTokenURI;
        _land = land;
        _openseaRegistryAddress = openseaRegistryAddress;
        _setDefaultRoyalty(msg.sender, 300);
    }

    // ------------------------------------------------------------------------

    /**
     * @dev Token URIs will be autogenerated based on `baseURI` and their token IDs.
     * See {ERC721-tokenURI}.
     */
    function _baseURI() internal view virtual override returns (string memory) {
        return _baseTokenURI;
    }

    function _isEstateShapeValid(uint256[] memory parcelIds)
        internal
        returns (bool)
    {
        if (parcelIds.length == 9) {
            // We expect a 3x3 matrix.
            // X checks
            require(
                parseToCoordinates(parcelIds[0])[0] + 1 ==
                    parseToCoordinates(parcelIds[1])[0]
            );
            require(
                parseToCoordinates(parcelIds[1])[0] + 1 ==
                    parseToCoordinates(parcelIds[2])[0]
            );
            require(
                parseToCoordinates(parcelIds[3])[0] + 1 ==
                    parseToCoordinates(parcelIds[4])[0]
            );
            require(
                parseToCoordinates(parcelIds[4])[0] + 1 ==
                    parseToCoordinates(parcelIds[5])[0]
            );
            require(
                parseToCoordinates(parcelIds[6])[0] + 1 ==
                    parseToCoordinates(parcelIds[7])[0]
            );
            require(
                parseToCoordinates(parcelIds[7])[0] + 1 ==
                    parseToCoordinates(parcelIds[8])[0]
            );
            // Y checks
            require(
                parseToCoordinates(parcelIds[0])[1] ==
                    parseToCoordinates(parcelIds[1])[1]
            );
            require(
                parseToCoordinates(parcelIds[1])[1] ==
                    parseToCoordinates(parcelIds[2])[1]
            );
            require(
                parseToCoordinates(parcelIds[3])[1] ==
                    parseToCoordinates(parcelIds[4])[1]
            );
            require(
                parseToCoordinates(parcelIds[4])[1] ==
                    parseToCoordinates(parcelIds[5])[1]
            );
            require(
                parseToCoordinates(parcelIds[6])[1] ==
                    parseToCoordinates(parcelIds[7])[1]
            );
            require(
                parseToCoordinates(parcelIds[7])[1] ==
                    parseToCoordinates(parcelIds[8])[1]
            );
            return true;
        } else if (parcelIds.length == 36) {
            return true;
        } else if (parcelIds.length == 81) {
            return true;
        } else if (parcelIds.length == 144) {
            return true;
        }
        return false;
    }

    function mintFromParcels(uint256[] memory tokenIds)
        public
        returns (uint256)
    {
        require(
            _isEstateShapeValid(tokenIds),
            "Invalid estate shape, must be square."
        );
        IHighriseLand(_land).bindToEstate(msg.sender, tokenIds);
        _tokenIds.increment();
        uint256 tokenId = _tokenIds.current();
        estatesToParcels[tokenId] = tokenIds;
        _mint(msg.sender, tokenId);
        return tokenId;
    }

    function burn(uint256 tokenId) public {
        require(
            _exists(tokenId),
            "ERC721: operator query for nonexistent token"
        );
        require(
            _isApprovedOrOwner(msg.sender, tokenId),
            "ERC721Burnable: caller is not owner nor approved"
        );
        uint256[] memory parcels = estatesToParcels[tokenId];
        for (uint256 i = 0; i < parcels.length; i++) {
            IERC721(_land).safeTransferFrom(
                address(this),
                msg.sender,
                parcels[i]
            );
        }
        _burn(tokenId);
    }

    // --------------------------------------- OVERRIDES ---------------------------------------------
    // The following functions are overrides required by Solidity.
    function _burn(uint256 tokenId)
        internal
        override(ERC721Upgradeable, ERC721RoyaltyUpgradeable)
    {
        super._burn(tokenId);
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId
    ) internal override(ERC721Upgradeable, ERC721EnumerableUpgradeable) {
        super._beforeTokenTransfer(from, to, tokenId);
    }

    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(
            ERC721Upgradeable,
            ERC721EnumerableUpgradeable,
            ERC721RoyaltyUpgradeable
        )
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    // -----------------------------------------------------------------------------------------------

    // ----------------------- HELPER LOGIC --------------------------------------------
    function ownerTokens(address owner) public view returns (uint256[] memory) {
        uint256 balance = balanceOf(owner);
        uint256[] memory tokens = new uint256[](balance);

        for (uint256 i = 0; i < balance; i++) {
            tokens[i] = tokenOfOwnerByIndex(owner, i);
        }

        return tokens;
    }

    // ---------------------------------------------------------------------------------

    // ----------------------- OPEN SEA REGISTRY ---------------------------------------
    /**
     * Override isApprovedForAll to whitelist user's OpenSea proxy accounts to enable gas-less listings.
     */
    function isApprovedForAll(address owner, address operator)
        public
        view
        override(ERC721Upgradeable, IERC721Upgradeable)
        returns (bool)
    {
        // Whitelist OpenSea proxy contract for easy trading.
        ProxyRegistry openseaRegistry = ProxyRegistry(_openseaRegistryAddress);
        if (address(openseaRegistry.proxies(owner)) == operator) {
            return true;
        }

        return super.isApprovedForAll(owner, operator);
    }

    /**
     * This is used instead of msg.sender as transactions won't be sent by the original token owner, but by OpenSea.
     */
    function _msgSender() internal view override returns (address sender) {
        return ContextMixin.msgSender();
    }
    // ---------------------------------------------------------------------------------
}
